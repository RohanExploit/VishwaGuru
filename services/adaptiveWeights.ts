import * as fs from 'fs';
import * as path from 'path';

export interface ModelWeights {
    severityWeights: Record<string, number>;
    duplicateThreshold: number;
    lastUpdated: string;
    previousWeights: Record<string, number>;
}

const defaultWeights: ModelWeights = {
    severityWeights: {
        'pothole': 5,
        'garbage': 4,
        'vandalism': 3,
        'water_leak': 6,
        'power_outage': 7
    },
    duplicateThreshold: 0.8,
    lastUpdated: new Date().toISOString(),
    previousWeights: {}
};

export class AdaptiveWeights {
    private weightsPath: string;

    constructor() {
        this.weightsPath = process.env.WEIGHTS_PATH || path.resolve(__dirname, '../data/modelWeights.json');
    }

    private loadWeights(): ModelWeights {
        if (!fs.existsSync(this.weightsPath)) {
            // Ensure directory exists
            fs.mkdirSync(path.dirname(this.weightsPath), { recursive: true });
            fs.writeFileSync(this.weightsPath, JSON.stringify(defaultWeights, null, 2));
            return defaultWeights;
        }

        try {
            const data = fs.readFileSync(this.weightsPath, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            console.error('Error reading weights, returning defaults.', error);
            return defaultWeights;
        }
    }

    private saveWeights(weights: ModelWeights) {
        fs.mkdirSync(path.dirname(this.weightsPath), { recursive: true });
        fs.writeFileSync(this.weightsPath, JSON.stringify(weights, null, 2));
    }

    adjustWeights(categorySpikes: Record<string, number>, highestSeverityRegion: string | null) {
        const currentWeights = this.loadWeights();

        // Audit trail: store a snapshot of previous state
        currentWeights.previousWeights = { ...currentWeights.severityWeights };

        let changed = false;

        // Adjust severity weights dynamically based on spikes
        for (const [category, spikePercentage] of Object.entries(categorySpikes)) {
            let weight = currentWeights.severityWeights[category] || 3; // base weight for unknown

            if (spikePercentage > 100) {
                weight += 1.5; // High urgency spike
            } else if (spikePercentage >= 50) {
                weight += 0.5; // Moderate spike
            }

            // Cap at 10
            currentWeights.severityWeights[category] = Math.min(10, Number(weight.toFixed(1)));
            changed = true;
        }

        // Adjust duplicate detection rule if clustering is found
        if (highestSeverityRegion) {
            // Decrease similarity threshold temporarily to catch more duplicates in high-density zones
            currentWeights.duplicateThreshold = Math.max(0.6, currentWeights.duplicateThreshold - 0.05);
            changed = true;
        } else {
            // Restore towards baseline if no clustering
            currentWeights.duplicateThreshold = Math.min(0.8, currentWeights.duplicateThreshold + 0.01);
            changed = true;
        }

        if (changed) {
            currentWeights.lastUpdated = new Date().toISOString();
            this.saveWeights(currentWeights);
        }

        return currentWeights;
    }
}
