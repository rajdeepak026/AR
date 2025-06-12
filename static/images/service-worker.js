// service-worker.js

// Event listener for the 'install' event
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installed');
    // Force the waiting service worker to become the active service worker
    // This ensures that the new service worker takes control immediately without requiring a page refresh.
    self.skipWaiting(); 
});

// Event listener for the 'activate' event
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activated');
    // Allows the service worker to take control of pages without a refresh
    // This is useful if the service worker updates and you want it to take effect on already open pages.
    event.waitUntil(self.clients.claim()); 
});

// Event listener for the 'push' event - This is triggered when your backend sends a push notification
self.addEventListener('push', (event) => {
    console.log('Service Worker: Push event received!');
    
    // Check if there is data in the push event
    const data = event.data ? event.data.json() : {};
    console.log('Push data received:', data);

    // Define the title and options for the notification
    const title = data.title || 'ApkaDr. Update'; // Default title
    const options = {
        body: data.body || 'You have a new update from ApkaDr.!', // Default body
        icon: data.icon || '/static/images/apkadr.logo.jpg', // Path to your app's icon
        badge: data.badge || '/static/images/apkadr.logo.jpg', // Badge for Android (small icon, typically monochrome)
        image: data.image || undefined, // Optional: large image URL
        data: { // Custom data payload that will be passed to notificationclick
            url: data.url || self.location.origin + '/my_appointments', // URL to open when notification is clicked
            // You can add more custom data here, e.g., appointmentId
            appointmentId: data.appointmentId || undefined
        },
        actions: data.actions || [], // Optional: array of action buttons for the notification
        vibrate: data.vibrate || [200, 100, 200], // Vibration pattern
        // Other useful options:
        // tag: 'appointment-status', // A tag to replace existing notifications with the same tag
        // renotify: true, // Show notification again if one with the same tag is already shown
        // sound: 'notification_sound.mp3' // Custom sound (browser support varies)
    };

    // Use event.waitUntil to keep the service worker alive until the notification is shown
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Event listener for the 'notificationclick' event - Triggered when a user clicks on the notification
self.addEventListener('notificationclick', (event) => {
    console.log('Service Worker: Notification clicked!');
    event.notification.close(); // Close the notification after it's clicked

    // Get the URL to open from the notification's data payload
    const urlToOpen = event.notification.data.url;

    // Use event.waitUntil to keep the service worker alive until the window is opened/focused
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }) // Find all open window clients
        .then((windowClients) => {
            let matchingClient = null;

            // Look for an existing client that already has the target URL open
            for (let i = 0; i < windowClients.length; i++) {
                const client = windowClients[i];
                if (client.url === urlToOpen) {
                    matchingClient = client;
                    break;
                }
            }

            if (matchingClient) {
                // If a matching client is found, focus it
                return matchingClient.focus();
            } else {
                // Otherwise, open a new window/tab to the URL
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

// Optional: Handle push subscription change
// This event is fired when a push subscription has been invalidated.
// You should resubscribe the user and update the subscription on your backend.
self.addEventListener('pushsubscriptionchange', function(event) {
    console.log('Service Worker: Push subscription changed. Resubscribing...');
    const options = event.oldSubscription.options; // Get old subscription options (including applicationServerKey)
    event.waitUntil(
        self.registration.pushManager.subscribe({
            userVisibleOnly: options.userVisibleOnly,
            applicationServerKey: options.applicationServerKey
        })
        .then(function(subscription) {
            console.log('New subscription obtained:', subscription);
            // Here you would typically send this new subscription to your backend
            // via a fetch request.
            // Example:
            // return fetch('/api/resubscribe', {
            //     method: 'POST',
            //     headers: {
            //         'Content-Type': 'application/json'
            //     },
            //     body: JSON.stringify(subscription)
            // });
        })
        .catch(function(e) {
            console.error('Error during pushsubscriptionchange:', e);
        })
    );
});