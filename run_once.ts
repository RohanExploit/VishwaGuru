import { DailyRefinementJob } from "./scheduler/dailyRefinementJob";

async function run() {
  const job = new DailyRefinementJob();
  await job.runRefinement();
  process.exit(0);
}

run();
