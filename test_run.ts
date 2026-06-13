import { DailyRefinementJob } from './scheduler/dailyRefinementJob';
const job = new DailyRefinementJob();
job.runRefinement().then(() => {
    console.log("Done");
    process.exit(0);
});
