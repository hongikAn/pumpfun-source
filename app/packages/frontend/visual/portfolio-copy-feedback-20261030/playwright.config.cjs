const path = require("node:path");
module.exports = {
  "testDir": path.resolve(__dirname, "../../tests"),
  "testMatch": [
    "portfolio.spec.ts"
  ],
  "grep": /reports actual clipboard denial/,
  "outputDir": path.resolve(__dirname, "../../test-results/portfolio-copy-feedback"),
  "workers": 1,
  "retries": 0,
  "reporter": "line",
  "use": {
    "baseURL": "http://127.0.0.1:3010",
    "viewport": {
      "width": 1280,
      "height": 900
    },
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
