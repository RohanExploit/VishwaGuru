import cron from 'node-cron';
import { PriorityEngine } from '../services/priorityEngine';

const priorityEngine = new PriorityEngine();

console.log('Daily Civic Intelligence Refinement Engine Scheduled.');
console.log('Running daily at 00:00 (Midnight).');

// Schedule job every day at midnight (00:00)
cron.schedule('0 0 * * *', async () => {
    try {
        console.log('\n=======================================');
        console.log('Starting Scheduled Daily Refinement Job');
        console.log('=======================================');
        await priorityEngine.runDailyRefinement();
    } catch (error) {
        console.error('Error executing daily refinement job:', error);
    }
});

// Allow immediate execution for testing or manual triggers
if (require.main === module) {
    (async () => {
        try {
            console.log('\n=======================================');
            console.log('Executing Immediate Daily Refinement Job');
            console.log('=======================================');
            await priorityEngine.runDailyRefinement();
        } catch (error) {
            console.error('Error executing manual daily refinement job:', error);
            process.exit(1);
        }
    })();
}
