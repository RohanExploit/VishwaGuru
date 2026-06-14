import { TrendAnalyzer } from '../services/trendAnalyzer';
import { AdaptiveWeights } from '../services/adaptiveWeights';
import { IntelligenceIndex } from '../services/intelligenceIndex';
import { Issue } from '../services/types';
import * as fs from 'fs';
import * as path from 'path';
import * as sqlite3 from 'sqlite3';

const TEST_DB_PATH = path.join(__dirname, 'test_app.db');

describe('Daily Civic Intelligence Refinement Engine Tests', () => {

  const dummyIssues: Issue[] = [
    {
      id: 1,
      description: "Huge pothole on main street. Dangerous for driving.",
      category: "Pothole",
      status: "open",
      created_at: new Date().toISOString(),
      upvotes: 2,
      latitude: 19.012,
      longitude: 72.843
    },
    {
      id: 2,
      description: "Another pothole nearby, causing severe traffic and driving issues.",
      category: "Pothole",
      status: "resolved",
      created_at: new Date().toISOString(),
      upvotes: 5,
      latitude: 19.014,
      longitude: 72.845
    },
    {
      id: 3,
      description: "Garbage pile causing bad smell and water pollution.",
      category: "Garbage",
      status: "open",
      created_at: new Date().toISOString(),
      upvotes: 1,
      latitude: 19.055,
      longitude: 72.890
    }
  ];

  describe('Unit Tests: TrendAnalyzer', () => {
    let analyzer: TrendAnalyzer;

    beforeEach(() => {
      analyzer = new TrendAnalyzer();
    });

    test('should extract top keywords excluding stop words', () => {
      const topKeywords = analyzer.getTopKeywords(dummyIssues, 3);
      expect(topKeywords.length).toBeLessThanOrEqual(3);
      // 'pothole', 'causing', 'driving' might be top
      expect(topKeywords).toContain('pothole');
      expect(topKeywords).not.toContain('the');
      expect(topKeywords).not.toContain('for');
    });

    test('should detect category spikes correctly', () => {
      const currentIssues = [...dummyIssues, ...dummyIssues]; // 4 potholes, 2 garbage
      const previousIssues = [dummyIssues[0], dummyIssues[2]]; // 1 pothole, 1 garbage

      const spikes = analyzer.detectCategorySpikes(currentIssues, previousIssues);

      // Pothole went 1 -> 4 (300% increase)
      // Garbage went 1 -> 2 (100% increase)
      expect(spikes).toHaveLength(2);
      expect(spikes[0].category).toBe('Pothole');
      expect(spikes[0].increasePercentage).toBe(300);
      expect(spikes[1].category).toBe('Garbage');
      expect(spikes[1].increasePercentage).toBe(100);
    });

    test('should identify geographic clustering', () => {
      const cluster = analyzer.identifyGeographicClustering(dummyIssues);
      expect(cluster).toBeDefined();
      expect(cluster!.latitude).toBe(19.01);
      expect(cluster!.longitude).toBe(72.84);
      expect(cluster!.count).toBe(2);
    });
  });

  describe('Integration Tests: AdaptiveWeights', () => {
    const testWeightsPath = path.join(__dirname, 'test_modelWeights.json');
    let adaptiveWeights: AdaptiveWeights;

    beforeEach(() => {
      adaptiveWeights = new AdaptiveWeights(testWeightsPath);
      if (fs.existsSync(testWeightsPath)) fs.unlinkSync(testWeightsPath);
    });

    afterAll(() => {
      if (fs.existsSync(testWeightsPath)) fs.unlinkSync(testWeightsPath);
    });

    test('should load default weights when file missing', () => {
      const weights = adaptiveWeights.loadWeights();
      expect(weights.categoryWeights['Pothole']).toBeDefined();
      expect(weights.duplicateThreshold).toBe(0.85);
    });

    test('should optimize and cap weights based on critical resolutions', () => {
      // 6 resolved Potholes
      const resolvedPotholes = Array(6).fill({ ...dummyIssues[1] });
      const currentWeights = adaptiveWeights.loadWeights();

      const optimized = adaptiveWeights.optimizeWeights(resolvedPotholes, currentWeights);

      expect(optimized.categoryWeights['Pothole']).toBeGreaterThan(currentWeights.categoryWeights['Pothole']);
      expect(optimized.history.length).toBe(1);
    });

    test('should dynamically adjust duplicate threshold based on volume', () => {
      const heavyTraffic = Array(150).fill({ ...dummyIssues[0] });
      const currentWeights = adaptiveWeights.loadWeights();

      const optimizedHeavy = adaptiveWeights.optimizeWeights(heavyTraffic, currentWeights);
      expect(optimizedHeavy.duplicateThreshold).toBeGreaterThan(currentWeights.duplicateThreshold);

      const lightTraffic = Array(10).fill({ ...dummyIssues[0] });
      const optimizedLight = adaptiveWeights.optimizeWeights(lightTraffic, currentWeights);
      expect(optimizedLight.duplicateThreshold).toBeLessThan(currentWeights.duplicateThreshold);
    });
  });

  describe('Integration Tests: IntelligenceIndex', () => {
    const testSnapshotsDir = path.join(__dirname, 'testSnapshots');
    let intelligenceIndex: IntelligenceIndex;

    beforeEach(() => {
      intelligenceIndex = new IntelligenceIndex(testSnapshotsDir);
      if (fs.existsSync(testSnapshotsDir)) {
        fs.rmSync(testSnapshotsDir, { recursive: true, force: true });
      }
      fs.mkdirSync(testSnapshotsDir);
    });

    afterAll(() => {
      if (fs.existsSync(testSnapshotsDir)) {
        fs.rmSync(testSnapshotsDir, { recursive: true, force: true });
      }
    });

    test('should generate and save daily snapshot score', () => {
      const snapshot = intelligenceIndex.generateIndex(
        dummyIssues,
        ['pothole', 'water'],
        [{ category: 'Garbage', increasePercentage: 100 }],
        { latitude: 19.0, longitude: 72.8, count: 5 }
      );

      expect(snapshot.indexScore).toBeGreaterThan(0);
      expect(snapshot.emergingConcerns[0].category).toBe('Garbage');

      intelligenceIndex.saveSnapshot(snapshot);

      const files = fs.readdirSync(testSnapshotsDir);
      expect(files.length).toBe(1);
      expect(files[0]).toContain(snapshot.date);
    });
  });

  describe('System Tests: Database Connections', () => {
    let db: sqlite3.Database;

    beforeAll((done) => {
      db = new sqlite3.Database(TEST_DB_PATH, (err) => {
        if (err) done(err);
        else {
          db.run(`
            CREATE TABLE issues (
              id INTEGER PRIMARY KEY,
              description TEXT,
              category TEXT,
              status TEXT,
              created_at DATETIME,
              upvotes INTEGER,
              latitude REAL,
              longitude REAL
            )
          `, done);
        }
      });
    });

    afterAll((done) => {
      db.close(() => {
        if (fs.existsSync(TEST_DB_PATH)) fs.unlinkSync(TEST_DB_PATH);
        done();
      });
    });

    test('should successfully connect to sqlite3 and execute a system query', (done) => {
      db.run(`
        INSERT INTO issues (description, category, status, created_at)
        VALUES ('Test Pothole', 'Pothole', 'open', datetime('now', '-2 hours'))
      `, function (err) {
        expect(err).toBeNull();
        db.all("SELECT * FROM issues WHERE category = 'Pothole'", (err, rows) => {
          expect(err).toBeNull();
          expect(rows.length).toBeGreaterThan(0);
          done();
        });
      });
    });
  });
});
