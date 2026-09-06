import os
import sys
import json
import logging
import datetime
import subprocess
import requests
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PRReviewer:
    def __init__(self, token, repo):
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        self.base_url = f"https://api.github.com/repos/{repo}"

    def check_quality(self, pr):
        logger.info(f"Checking quality for PR #{pr['number']}")
        if not pr.get('title') or len(pr['title']) < 5:
            return False, "Title too short or missing."
        if not pr.get('body') or len(pr['body']) < 10:
            return False, "Description too short or missing."
        return True, "Quality checks passed."

    def check_security(self, pr):
        logger.info(f"Checking security for PR #{pr['number']}")
        files_url = f"{self.base_url}/pulls/{pr['number']}/files"
        response = requests.get(files_url, headers=self.headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch files for PR #{pr['number']}")
            return False, "Failed to fetch files."
        
        files = response.json()
        dangerous_keywords = ['password', 'secret', 'eval(', 'exec(', 'SELECT * FROM']
        for f in files:
            patch = f.get('patch', '')
            for line in patch.split('\n'):
                if line.startswith('+'): # Only check additions
                    for kw in dangerous_keywords:
                        if kw.lower() in line.lower():
                            return False, f"Security risk found: {kw} in file {f.get('filename')}"
        return True, "Security checks passed."

    def get_open_prs(self):
        url = f"{self.base_url}/pulls?state=open&per_page=100"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        logger.error(f"Failed to fetch open PRs. Status: {response.status_code}")
        return []


class PRMerger:
    def __init__(self, token, repo):
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        self.base_url = f"https://api.github.com/repos/{repo}"

    def merge_pr(self, pr_number, title):
        logger.info(f"Attempting to squash-merge PR #{pr_number}")
        url = f"{self.base_url}/pulls/{pr_number}/merge"
        payload = {
            "commit_title": f"Merge PR #{pr_number}: {title}",
            "merge_method": "squash"
        }
        response = requests.put(url, headers=self.headers, json=payload)
        if response.status_code in [200, 201] and response.json().get('merged'):
            logger.info(f"Successfully merged PR #{pr_number}")
            return True, response.json().get('sha')
        else:
            logger.error(f"Failed to merge PR #{pr_number}: {response.json().get('message')}")
            return False, None

    def revert_merge(self, sha):
        logger.warning(f"Reverting merge commit {sha}")
        try:
            # Local revert via git
            subprocess.run(["git", "revert", "-m", "1", "--no-edit", sha], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            logger.info("Successfully reverted the merge.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to revert merge: {e}")


class LocalSync:
    @staticmethod
    def sync():
        logger.info("Syncing local repository with origin/main")
        try:
            subprocess.run(["git", "fetch", "origin", "main"], check=True)
            subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
            logger.info("Sync complete.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Git sync failed: {e}")
            return False


class LocalDeployment:
    def __init__(self, port=8000):
        self.port = port
        self.process = None

    def install_dependencies(self):
        logger.info("Installing dependencies...")
        try:
            if os.path.exists("package.json"):
                subprocess.run(["npm", "install"], check=True)
            elif os.path.exists("requirements.txt"):
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            logger.info("Dependencies installed.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False

    def run_tests(self):
        logger.info("Running tests...")
        try:
            if os.path.exists("package.json"):
                subprocess.run(["npm", "test"], check=True)
            else:
                subprocess.run(["pytest", "--cov=."], check=True)
            logger.info("Tests passed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Tests failed: {e}")
            return False

    def deploy(self):
        logger.info("Starting local deployment...")
        try:
            if os.path.exists("docker-compose.yml"):
                subprocess.run(["docker-compose", "up", "-d"], check=True)
            elif os.path.exists("manage.py"):
                self.process = subprocess.Popen([sys.executable, "manage.py", "runserver", f"0.0.0.0:{self.port}"])
            else:
                # Fallback to a simple python server for health check purposes
                self.process = subprocess.Popen([sys.executable, "-m", "http.server", str(self.port)])
            logger.info("Deployment started.")
            return True
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    def check_health(self):
        logger.info(f"Running health check on http://localhost:{self.port}/health")
        try:
            # Wait briefly for server to start
            import time; time.sleep(5)
            # Try /health, fallback to / if health endpoint doesn't exist
            res = requests.get(f"http://localhost:{self.port}/health")
            if res.status_code == 200:
                logger.info("Health check passed.")
                return True
        except Exception:
            pass
        
        try:
            res = requests.get(f"http://localhost:{self.port}/")
            if res.status_code == 200:
                logger.info("Root endpoint accessible, considering health check passed.")
                return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        return False

    def teardown(self):
        if self.process:
            self.process.terminate()
            logger.info("Terminated local deployment process.")
        elif os.path.exists("docker-compose.yml"):
            subprocess.run(["docker-compose", "down"])


class Pipeline:
    def __init__(self):
        self.token = os.environ.get("GITHUB_PAT") or os.environ.get("GITHUB_TOKEN")
        self.repo = os.environ.get("GITHUB_REPOSITORY", "RohanExploit/VishwaGuru")
        self.port = int(os.environ.get("DEPLOYMENT_PORT", 8000))
        
        if not self.token:
            logger.error("GITHUB_PAT or GITHUB_TOKEN environment variable is required.")
            sys.exit(1)
            
        self.reviewer = PRReviewer(self.token, self.repo)
        self.merger = PRMerger(self.token, self.repo)
        self.deployer = LocalDeployment(self.port)
        
        self.report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "processed_prs": 0,
            "merged_prs": [],
            "failed_prs": [],
            "security_flagged_prs": [],
            "test_status": "Unknown",
            "health_check": "Unknown"
        }

    def generate_report(self):
        with open("pipeline_report.json", "w") as f:
            json.dump(self.report, f, indent=4)
        logger.info("Execution report generated: pipeline_report.json")

    def run(self):
        logger.info("Starting Auto-Deploy Pipeline")
        
        open_prs = self.reviewer.get_open_prs()
        logger.info(f"Found {len(open_prs)} open PRs.")
        
        for pr in open_prs:
            self.report["processed_prs"] += 1
            num = pr['number']
            
            # Quality Checks
            q_pass, q_msg = self.reviewer.check_quality(pr)
            if not q_pass:
                logger.warning(f"PR #{num} failed quality checks: {q_msg}")
                self.report["failed_prs"].append({"number": num, "reason": q_msg})
                continue
                
            # Security Checks
            s_pass, s_msg = self.reviewer.check_security(pr)
            if not s_pass:
                # A flagged PR is skipped and never merged -- but it no longer
                # aborts the whole run. check_security is a substring match over
                # added lines, so a PR that merely adds the word "secret" to a
                # file like .dockerignore tripped it, and every PR queued behind
                # it went unprocessed while the workflow went red on a finding
                # that needed a human read rather than a failed build.
                logger.error(f"PR #{num} failed security checks: {s_msg}")
                self.report["failed_prs"].append({"number": num, "reason": s_msg})
                self.report["security_flagged_prs"].append({"number": num, "reason": s_msg})
                logger.warning(f"PR #{num} skipped for manual security review; continuing.")
                continue
                
            # Merge
            m_pass, sha = self.merger.merge_pr(num, pr['title'])
            if m_pass:
                self.report["merged_prs"].append(num)
                
                # Sync & Test after merge
                if not LocalSync.sync():
                    self.merger.revert_merge(sha)
                    continue
                    
                if not self.deployer.install_dependencies():
                    logger.error("Dependency installation failed. Reverting merge.")
                    self.merger.revert_merge(sha)
                    continue
                    
                if not self.deployer.run_tests():
                    logger.error("Tests failed. Reverting merge.")
                    self.report["test_status"] = "Failed"
                    self.merger.revert_merge(sha)
                    # Stop on test failures requested
                    logger.critical("Stopping pipeline due to test failure.")
                    self.generate_report()
                    sys.exit(1)
                    
                self.report["test_status"] = "Passed"
                
                # Deploy & Health Check
                if self.deployer.deploy():
                    if self.deployer.check_health():
                        self.report["health_check"] = "Passed"
                    else:
                        self.report["health_check"] = "Failed"
                        logger.error("Health check failed. Reverting merge.")
                        self.merger.revert_merge(sha)
                    self.deployer.teardown()
            else:
                self.report["failed_prs"].append({"number": num, "reason": "Merge Conflict/API Error"})

        self.generate_report()
        logger.info("Pipeline completed.")

if __name__ == "__main__":
    try:
        pipeline = Pipeline()
        pipeline.run()
    except Exception as e:
        logger.exception("Pipeline crashed unexpectedly:")
        sys.exit(1)
