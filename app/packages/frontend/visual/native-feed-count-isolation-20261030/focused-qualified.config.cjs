module.exports = {
 testDir: "C:\\Users\\ahi20\\Documents\\ChatGPT\\pumpfun-contribution-review\\app-batch-20261029\\wt-frontend-data\\app\\packages\\frontend\\tests", testMatch: 'native-home-feed.spec.ts',
 outputDir: "C:\\Users\\ahi20\\Documents\\ChatGPT\\pumpfun-contribution-review\\app-native-feed-count-isolation-20261030\\focused-qualified", fullyParallel: false, forbidOnly: true,
 retries: 0, workers: 1, reporter: 'line', timeout: 60000,
 grep: /retains validated newest callouts|keeps newest pagination|fails closed for unavailable/,
 use: {baseURL: 'http://127.0.0.1:3011', browserName: 'chromium',
 viewport: {width: 1280, height: 800},
 storageState: {cookies: [{name:'clickwrap_accepted',value:'true',domain:'127.0.0.1',path:'/',expires:-1,httpOnly:false,secure:false,sameSite:'Lax'}],origins:[]},
 screenshot: 'only-on-failure', video: 'on', trace:'on'}
};
