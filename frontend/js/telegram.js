/**
 * Telegram WebApp Integration & Haptic Feedback Helper
 */
const TelegramHelper = (() => {
  const tg = window.Telegram?.WebApp;
  
  // Default mock user for browser preview
  let user = {
    id: 999001,
    first_name: "Hasan",
    username: "hasan_dev"
  };

  if (tg) {
    try {
      tg.ready();
      tg.expand();
      
      // Auto theme color adaptation
      if (tg.setHeaderColor) {
        tg.setHeaderColor('#0B0F17');
      }
      if (tg.setBackgroundColor) {
        tg.setBackgroundColor('#0B0F17');
      }
      
      if (tg.initDataUnsafe?.user) {
        user = tg.initDataUnsafe.user;
      }
    } catch (e) {
      console.warn("Telegram WebApp initialization error:", e);
    }
  }

  function triggerHaptic(type = 'light') {
    if (!tg?.HapticFeedback) return;
    try {
      switch (type) {
        case 'light':
          tg.HapticFeedback.impactOccurred('light');
          break;
        case 'medium':
          tg.HapticFeedback.impactOccurred('medium');
          break;
        case 'heavy':
          tg.HapticFeedback.impactOccurred('heavy');
          break;
        case 'success':
          tg.HapticFeedback.notificationOccurred('success');
          break;
        case 'warning':
          tg.HapticFeedback.notificationOccurred('warning');
          break;
        case 'error':
          tg.HapticFeedback.notificationOccurred('error');
          break;
        default:
          tg.HapticFeedback.impactOccurred('light');
      }
    } catch (e) {
      console.warn("Haptic feedback error:", e);
    }
  }

  return {
    tg,
    user,
    triggerHaptic
  };
})();
