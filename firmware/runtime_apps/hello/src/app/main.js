// Core may evaluate this entry again in the same JS realm after stop.
(() => {
  // Navigation state belongs to ESPocket. Only confirmation UI state lives here.
  const navigate = async request => JSON.parse(await espocketNavigation.dispatch(JSON.stringify(request)));
  const service = (name, operation, parameters) =>
    brookesia.call_service_function(name, operation, JSON.stringify(parameters));
  let alive = false;
  let polling = false;
  let confirm = false;
  let pendingToken = null;
  let epoch = 0;

  function feedback(text) {
    service('SystemGui', 'SetText', {Path: '/detail/hint', Text: text});
  }

  globalThis.brookesia_app = {
    on_start() {
      ++epoch;
      alive = true;
      confirm = false;
      pendingToken = null;
      polling = false;
      for (const action of ['open_detail', 'toggle_confirm', 'allow_back', 'cancel_back']) {
        service('SystemGui', 'SubscribeAction', {Action: action});
      }
      // Only refresh confirmation UI here; framework owns the async completion pump.
      service('SystemTimer', 'StartPeriodic', {Name: 'navigation', IntervalMs: 100});
    },
    on_stop() { ++epoch; alive = false; pendingToken = null; },
    async on_action(action) {
      const task = epoch;
      try {
        if (action === 'open_detail') await navigate({operation: 'push', pageId: 'detail'});
        else if (action === 'toggle_confirm') {
          await navigate({operation: 'setBackDecision', decision: confirm ? 'allow' : 'defer'});
          if (!alive || task !== epoch) return;
          confirm = !confirm;
          service('SystemGui', 'SetText', {Path: '/detail/confirm/label', Text: `Confirm Back: ${confirm ? 'On' : 'Off'}`});
        } else if (action === 'allow_back' || action === 'cancel_back') {
          if (!pendingToken) { feedback('No pending Back'); return; }
          await navigate({operation: 'completeBack', token: pendingToken, allow: action === 'allow_back'});
          if (!alive || task !== epoch) return;
          pendingToken = null;
          if (alive && action === 'cancel_back') feedback('Back cancelled');
        }
      } catch (error) {
        console.log(`Navigation error: ${error}`);
        if (alive && task === epoch) feedback(String(error));
      }
    },
    async on_timer(_id, name) {
      if (name !== 'navigation' || polling || !alive) return;
      polling = true;
      const task = epoch;
      try {
        const page = await navigate({operation: 'snapshot'});
        if (!alive || task !== epoch) return;
        const wasPending = pendingToken !== null;
        pendingToken = page.pendingToken;
        if (pendingToken) feedback('Back pending: allow or cancel');
        else if (wasPending && page.pageId === 'detail') feedback('Back cleared; still in Detail');
      } catch (error) { console.log(`Navigation snapshot error: ${error}`); }
      finally { if (task === epoch) polling = false; }
    }
  };
})();
