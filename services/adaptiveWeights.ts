import fs from 'fs';
import path from 'path';
import { WeightUpdate } from './priorityEngine';

export class AdaptiveWeights {
    private fileLocation: string;
    private weights: any;

    constructor(fileLocation: string = './data/modelWeights.json') {
        this.fileLocation = fileLocation;
        this.loadWeights();
    }

    private loadWeights() {
        if (!fs.existsSync(this.fileLocation)) {
            this.weights = {
                category_multipliers: {},
                duplicate_search_radius: 50.0,
                audit_history: []
            };
            return;
        }

        try {
            const data = fs.readFileSync(this.fileLocation, 'utf-8');
            this.weights = JSON.parse(data);
        } catch (e) {
            console.error("Error loading adaptive weights:", e);
            this.weights = {};
        }

        if (!this.weights.audit_history) {
            this.weights.audit_history = [];
        }
    }

    private saveWeights() {
        try {
            fs.writeFileSync(this.fileLocation, JSON.stringify(this.weights, null, 2));
        } catch (e) {
            console.error("Error saving adaptive weights:", e);
        }
    }

    private _recordAudit(reason: string, oldValue: any, newValue: any, key: string) {
        this.weights.audit_history.push({
            timestamp: new Date().toISOString(),
            key,
            oldValue,
            newValue,
            reason
        });
    }

    /**
     * Integrates severity updates dynamically adjusting the weights logic.
     */
    public updateCategoryWeights(updates: WeightUpdate[]): any[] {
        const changes = [];
        for (const update of updates) {
            const oldWeight = this.weights.category_multipliers[update.category] || 1.0;
            let newWeight = oldWeight * update.factor;
            newWeight = Math.max(0.5, Math.min(3.0, newWeight)); // Clamp

            this.weights.category_multipliers[update.category] = newWeight;

            changes.push({
                category: update.category,
                old_weight: oldWeight,
                new_weight: newWeight,
                reason: update.reason
            });

            this._recordAudit(update.reason, oldWeight, newWeight, `category_multipliers.${update.category}`);
        }

        if (updates.length > 0) {
            this.saveWeights();
        }

        return changes;
    }

    /**
     * Updates Duplicate radius dynamically
     */
    public updateDuplicateRadius(clusterCount: number, issuesCount: number): any {
        const currentRadius = this.weights.duplicate_search_radius || 50.0;
        let factor = 1.0;
        let reason = `Cluster density analysis (clusters: ${clusterCount}, issues: ${issuesCount})`;

        if (clusterCount > 5) {
            factor = 1.05;
        } else if (clusterCount === 0 && issuesCount > 50) {
            factor = 1.05;
        } else if (issuesCount < 10 && currentRadius > 50) {
            factor = 0.95;
        }

        if (factor !== 1.0) {
            let newRadius = currentRadius * factor;
            newRadius = Math.max(10.0, Math.min(200.0, newRadius)); // Clamp

            this.weights.duplicate_search_radius = newRadius;

            this._recordAudit(reason, currentRadius, newRadius, 'duplicate_search_radius');
            this.saveWeights();

            return {
                category: "GLOBAL_DUPLICATE_RADIUS",
                old_weight: currentRadius,
                new_weight: newRadius,
                reason
            };
        }

        return null;
    }

    public getWeights() {
        return this.weights;
    }
}
