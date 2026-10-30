module.exports = {
 testDir: "C:\\Users\\ahi20\\Documents\\ChatGPT\\pumpfun-contribution-review\\app-batch-20261029\\wt-frontend-data\\app\\packages\\frontend\\tests", testMatch: 'live.spec.ts', outputDir: "C:\\Users\\ahi20\\Documents\\ChatGPT\\pumpfun-contribution-review\\app-live-inspect-focus-20261030\\focused",
 fullyParallel: false, forbidOnly: true, retries:0, workers:1, reporter:'line',timeout:60000,
 grep: /Inspect reveals selected metadata|a direct archived selection does not request metadata focus/,
 use:{baseURL:'http://127.0.0.1:3010',browserName:'chromium',
 storageState:{cookies:[{name:'clickwrap_accepted',value:'true',domain:'127.0.0.1',path:'/',expires:-1,httpOnly:false,secure:false,sameSite:'Lax'}],origins:[]},
 screenshot:'only-on-failure',video:'on',trace:'on'}
};
