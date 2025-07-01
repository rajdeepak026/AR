window.OneSignalDeferred.push(async function(OneSignal) {
  await OneSignal.init({
    appId: "b247bbe3-988e-4438-b5b2-74207755fea4",
    notifyButton: { enable: true }, // optional UI
    allowLocalhostAsSecureOrigin: true // only for dev
  });

  const isPushSupported = await OneSignal.isPushNotificationsSupported();
  if (isPushSupported) {
    const permission = await OneSignal.getNotificationPermission();
    if (permission === 'granted') {
      const userId = await OneSignal.getUserId(); // This is the player_id
      if (userId) {
        fetch('/save_player_id', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ player_id: userId })
        });
      }
    } else {
      console.warn('Notification permission not granted:', permission);
    }
  } else {
    console.warn('Push notifications are not supported');
  }
});
