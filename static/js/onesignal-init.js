window.OneSignal = window.OneSignal || [];
OneSignal.push(function () {
  OneSignal.init({
    appId: "b247bbe3-988e-4438-b5b2-74207755fea4",
    serviceWorkerPath: "https://apkadr.in/OneSignalSDKWorker.js",
    serviceWorkerUpdaterPath: "https://apkadr.in/OneSignalSDKUpdaterWorker.js",
    serviceWorkerParam: { scope: "/" },
    notifyButton: {
      enable: true,
    },
  });
});
