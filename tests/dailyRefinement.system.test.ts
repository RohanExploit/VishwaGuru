import * as sqlite3 from "sqlite3";
import * as path from "path";
import * as fs from "fs";

// Mock DB_PATH
const TEST_DB_PATH = path.join(__dirname, "system_test_issues.db");
const TEST_WEIGHTS_PATH = path.join(__dirname, "../data/modelWeights.json");
const TEST_SNAPSHOTS_DIR = path.join(__dirname, "../data/dailySnapshots");

process.env.DB_PATH = TEST_DB_PATH;

import { DailyRefinementJob } from "../scheduler/dailyRefinementJob";

describe("DailyRefinementJob System Tests", () => {
  let db: sqlite3.Database;
  let job: DailyRefinementJob;

  beforeAll((done) => {
    // Ensure test directories exist
    if (!fs.existsSync(path.join(__dirname, "../data"))) {
      fs.mkdirSync(path.join(__dirname, "../data"), { recursive: true });
    }
    if (!fs.existsSync(TEST_SNAPSHOTS_DIR)) {
      fs.mkdirSync(TEST_SNAPSHOTS_DIR, { recursive: true });
    }

    db = new sqlite3.Database(TEST_DB_PATH, (err) => {
      if (err) return done(err);

      db.run(
        `CREATE TABLE issues (
          id INTEGER PRIMARY KEY,
          description TEXT,
          category TEXT,
          status TEXT,
          created_at DATETIME,
          upvotes INTEGER,
          latitude REAL,
          longitude REAL
        )`,
        (err) => {
          if (err) return done(err);

          // Insert dummy data
          db.run(
            `INSERT INTO issues (description, category, status, created_at, latitude, longitude) VALUES
              ('huge pothole', 'Pothole', 'resolved', datetime('now', '-2 hours'), 19.0, 72.8),
              ('pothole again', 'Pothole', 'resolved', datetime('now', '-3 hours'), 19.0, 72.8),
              ('garbage everywhere', 'Garbage', 'open', datetime('now', '-4 hours'), 19.1, 72.9),
              ('pothole fixed', 'Pothole', 'resolved', datetime('now', '-5 hours'), 19.0, 72.8),
              ('pothole very bad', 'Pothole', 'resolved', datetime('now', '-1 hours'), 19.0, 72.8),
              ('pothole dangerous', 'Pothole', 'resolved', datetime('now', '-6 hours'), 19.0, 72.8),
              ('pothole resolved', 'Pothole', 'resolved', datetime('now', '-10 hours'), 19.0, 72.8)
            `,
            (err) => {
              if (err) return done(err);
              job = new DailyRefinementJob();
              done();
            }
          );
        }
      );
    });
  });

  afterAll((done) => {
    db.close((err) => {
      if (fs.existsSync(TEST_DB_PATH)) fs.unlinkSync(TEST_DB_PATH);
      if (fs.existsSync(TEST_WEIGHTS_PATH)) fs.unlinkSync(TEST_WEIGHTS_PATH);
      // Clean up snapshots created today
      const files = fs.readdirSync(TEST_SNAPSHOTS_DIR);
      for (const file of files) {
          fs.unlinkSync(path.join(TEST_SNAPSHOTS_DIR, file));
      }
      done();
    });
  });

  test("runRefinement should execute successfully and update weights and snapshots", async () => {
    // Before run, capture initial state if any
    const initialSnapshotsCount = fs.readdirSync(TEST_SNAPSHOTS_DIR).length;

    await job.runRefinement();

    // Verify weights updated
    expect(fs.existsSync(TEST_WEIGHTS_PATH)).toBe(true);
    const weights = JSON.parse(fs.readFileSync(TEST_WEIGHTS_PATH, "utf8"));
    // Since we inserted 6 resolved potholes, it should boost the weight for Pothole
    expect(weights.categoryWeights.Pothole).toBeGreaterThan(1.0); // Assuming 1.0 is default, might be different. Let's just check it exists.
    expect(weights.categoryWeights.Pothole).toBeDefined();

    // Verify snapshot generated
    const newSnapshotsCount = fs.readdirSync(TEST_SNAPSHOTS_DIR).length;
    expect(newSnapshotsCount).toBe(initialSnapshotsCount + 1);

    const snapshotFiles = fs.readdirSync(TEST_SNAPSHOTS_DIR);
    const latestSnapshotFile = snapshotFiles[snapshotFiles.length - 1];
    const snapshotData = JSON.parse(fs.readFileSync(path.join(TEST_SNAPSHOTS_DIR, latestSnapshotFile), "utf8"));

    expect(snapshotData.indexScore).toBeDefined();
    expect(snapshotData.emergingConcerns).toBeDefined();
    // Pothole has a spike because there are 6 vs 0 in previous 24h
    expect(snapshotData.emergingConcerns.length).toBeGreaterThan(0);
    expect(snapshotData.emergingConcerns[0].category).toBe("Pothole");
  });
});
