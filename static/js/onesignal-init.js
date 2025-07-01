window.OneSignal = window.OneSignal || [];
OneSignal.push(function () {
  console.log("Initializing OneSignal...");

  OneSignal.init({
    appId: "b247bbe3-988e-4438-b5b2-74207755fea4",
    allowLocalhostAsSecureOrigin: true,
    notifyButton: {
      enable: true,
    },
  });

  // 🔄 After initialization, get and store the player's ID
  OneSignal.getUserId().then(function (playerId) {
    console.log("OneSignal Player ID:", playerId);
    if (playerId) {
      // Send the player ID to your Flask backend with the correct field name: fcm_token
      fetch("/store_player_id", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fcm_token: playerId })
      }).then(res => {
        if (res.ok) {
          console.log("Player ID stored successfully.");
        } else {
          console.warn("Failed to store player ID.");
        }
      });
    }
  });
});
