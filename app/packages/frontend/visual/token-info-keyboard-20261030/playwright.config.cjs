const path = require("node:path");
module.exports = {
  "testDir": path.resolve(__dirname, "../../tests"),
  "testMatch": [
    "token-info-keyboard.spec.ts"
  ],
  "outputDir": process.env.PLAYWRIGHT_OUTPUT_DIR || path.resolve(__dirname, "../../test-results/token-info-keyboard"),
  "fullyParallel": false,
  "forbidOnly": true,
  "retries": 0,
  "workers": 1,
  "reporter": "line",
  "use": {
    "baseURL": "http://127.0.0.1:3010",
    "browserName": "chromium",
    "storageState": {
      "cookies": [
        {
          "name": "clickwrap_accepted",
          "value": "true",
          "domain": "127.0.0.1",
          "path": "/",
          "expires": -1,
          "httpOnly": false,
          "secure": false,
          "sameSite": "Lax"
        }
      ],
      "origins": []
    },
    "screenshot": "only-on-failure",
    "trace": "retain-on-failure",
    "video": "on"
  }
};
