self.addEventListener('push', (event) => {
  let data = { title: 'NexUacademy', body: 'You have a new notification' };
  try {
    data = event.data.json();
  } catch (e) {
    data.body = event.data.text();
  }

  const options = {
    body: data.body,
    icon: '/logo.png',
    badge: '/logo.png',
    data: data.data || {},
    vibrate: [200, 100, 200],
    requireInteraction: true,
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data.url || '/dashboard';
  event.waitUntil(clients.openWindow(url));
});
