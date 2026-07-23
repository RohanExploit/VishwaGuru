import { TrendAnalyzer } from '../services/trendAnalyzer';
import { AdaptiveWeights } from '../services/adaptiveWeights';
import { PriorityEngine } from '../services/priorityEngine';
import { IntelligenceIndex } from '../services/intelligenceIndex';
import sqlite3 from 'sqlite3';
import fs from 'fs';
import path from 'path';

describe('Daily Civic Intelligence Refinement Engine', () => {

  describe('TrendAnalyzer', () => {
    let dbPath: string;
    let analyzer: TrendAnalyzer;

    beforeAll((done) => {
      dbPath = path.resolve(__dirname, 'test_issues.db');
      if (fs.existsSync(dbPath)) {
        try { fs.unlinkSync(dbPath); } catch (e) {}
      }
      const db = new sqlite3.Database(dbPath);
      db.serialize(() => {
        db.run('CREATE TABLE issues (id INTEGER PRIMARY KEY, description TEXT, category TEXT, location TEXT, created_at DATETIME)');

        const stmt = db.prepare('INSERT INTO issues (description, category, location, created_at) VALUES (?, ?, ?, ?)');
        const now = new Date().toISOString();

        stmt.run('Huge pothole on main street, dangerous pothole', 'infrastructure', 'Ward 1', now);
        stmt.run('Water supply is completely broken', 'water', 'Ward 2', now);
        stmt.run('Another pothole here', 'infrastructure', 'Ward 1', now);

        stmt.finalize(() => {
          db.close(done);
        });
      });
    });

    afterAll((done) => {
      setTimeout(() => {
        if (fs.existsSync(dbPath)) {
          try { fs.unlinkSync(dbPath); } catch (e) {}
        }
        done();
      }, 500); // wait for locks to release
    });

    it('should correctly analyze trends in the last 24 hours', async () => {
      analyzer = new TrendAnalyzer(dbPath);
      const results = await analyzer.analyzeLast24Hours();

      expect(results.totalIssues).toBe(3);
      expect(results.categorySpikes['infrastructure']).toBe(2);
      expect(results.categorySpikes['water']).toBe(1);
      expect(results.topKeywords).toContain('pothole');
      expect(results.locations).toContain('Ward 1');
      expect(results.locations).toContain('Ward 2');

      analyzer.close();
    });
  });

  describe('AdaptiveWeights', () => {
    const testWeightsPath = path.resolve(__dirname, 'test_weights.json');
    let adapter: AdaptiveWeights;

    beforeEach(() => {
      if (fs.existsSync(testWeightsPath)) fs.unlinkSync(testWeightsPath);
      adapter = new AdaptiveWeights(testWeightsPath);
    });

    afterAll(() => {
      if (fs.existsSync(testWeightsPath)) fs.unlinkSync(testWeightsPath);
    });

    it('should adjust weights based on spikes', () => {
      // 10 issues total, 6 infrastructure, 4 water. Both > 10%
      const newWeights = adapter.optimizeWeights({ 'infrastructure': 6, 'water': 4 }, 10);

      expect(newWeights['infrastructure']).toBe(1.1);
      expect(newWeights['water']).toBe(1.1);

      // The file should be created
      expect(fs.existsSync(testWeightsPath)).toBe(true);
      const savedData = JSON.parse(fs.readFileSync(testWeightsPath, 'utf8'));
      expect(savedData.current).toEqual(newWeights);
      expect(savedData.history.length).toBe(1);
    });
  });

  describe('PriorityEngine', () => {
    const priority = new PriorityEngine();

    it('should adjust threshold based on volume', () => {
      expect(priority.adjustDuplicateThreshold(50)).toBe(0.85);
      expect(priority.adjustDuplicateThreshold(150)).toBe(0.80);
      expect(priority.adjustDuplicateThreshold(600)).toBe(0.75);
      expect(priority.adjustDuplicateThreshold(1500)).toBe(0.70);
    });
  });

  describe('IntelligenceIndex', () => {
    const testHistoryPath = path.resolve(__dirname, 'test_history.json');
    let indexer: IntelligenceIndex;

    beforeEach(() => {
      if (fs.existsSync(testHistoryPath)) fs.unlinkSync(testHistoryPath);
      indexer = new IntelligenceIndex(testHistoryPath);
    });

    afterAll(() => {
      if (fs.existsSync(testHistoryPath)) fs.unlinkSync(testHistoryPath);
    });

    it('should calculate index correctly', () => {
      const result = indexer.calculateDailyIndex(
        30, // low issues -> +5 score
        ['pothole', 'water'],
        { 'infrastructure': 20, 'water': 10 },
        ['Ward 1', 'Ward 2']
      );

      expect(result.index).toBe(55.0); // 50.0 + 5.0
      expect(result.diff).toBe(5.0);
      expect(result.topConcern).toBe('infrastructure');
      expect(result.highestSeverityRegion).toBe('Ward 1');

      const savedData = JSON.parse(fs.readFileSync(testHistoryPath, 'utf8'));
      expect(savedData.length).toBe(1);
      expect(savedData[0].index).toBe(55.0);
    });
  });
});
