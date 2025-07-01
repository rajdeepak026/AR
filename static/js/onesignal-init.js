// Ensure OneSignalDeferred is defined
window.OneSignalDeferred = window.OneSignalDeferred || [];

// Add your init logic to the queue
window.OneSignalDeferred.push(async function (OneSignal) {
  await OneSignal.init({
    appId: "b247bbe3-988e-4438-b5b2-74207755fea4",
    notifyButton: { enable: true },
    allowLocalhostAsSecureOrigin: true // Remove in production if not needed
  });

  const isPushSupported = await OneSignal.isPushNotificationsSupported();
  if (isPushSupported) {
    const permission = await OneSignal.getNotificationPermission();
    if (permission === 'granted') {
      const userId = await OneSignal.getUserId();
      if (userId) {
        console.log("📬 Player ID:", userId);
        fetch('/save_player_id', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ player_id: userId })
        });
      }
    }
  } else {
    console.warn("Push notifications not supported in this browser.");
  }
});
