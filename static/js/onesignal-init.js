window.OneSignal = window.OneSignal || [];
OneSignal.push(function () {
  console.log("Initializing OneSignal...");

  OneSignal.init({
    appId: "b247bbe3-988e-4438-b5b2-74207755fea4",
    notifyButton: { enable: true },
    allowLocalhostAsSecureOrigin: true
  });

  OneSignal.getUserId().then(function(playerId) {
    console.log("OneSignal Player ID:", playerId);
    if (playerId) {
      fetch("/store_player_id", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fcm_token: playerId })
      });
    }
  });
});
