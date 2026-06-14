import { DailyRefinementJob } from "./scheduler/dailyRefinementJob";

async function main() {
    const job = new DailyRefinementJob();
    await job.runRefinement();
    process.exit(0);
}

main();
