// Temporary hidden Runtime fixture; never stage into a production package.
// Prepend globalThis.keyboardIsolation = {failStop: boolean} during preparation.
(() => {
  const config = globalThis.keyboardIsolation;
  let ticks = 0;
  globalThis.brookesia_app = {
    on_start() {
      brookesia.subscribe_service_event('SystemCore', 'KeyboardClosed');
      brookesia.subscribe_service_event('Display', 'BacklightBrightnessChanged');
      brookesia.call_service_function('SystemTimer', 'StartPeriodic',
        JSON.stringify({Name: 'isolation-canary', IntervalMs: 200}));
      console.log('KISO OBSERVER_STARTED');
    },
    on_event(service, event) {
      // Never log received payloads, even when testing a privacy defect.
      if (service === 'SystemCore' && event === 'KeyboardClosed')
        console.log('KISO FAIL_CROSS_OWNER_RESULT');
      else console.log(`KISO OBSERVER_PUBLIC_EVENT ${config.failStop ? 1 : 0}`);
    },
    on_timer(_id, name) {
      if (name === 'isolation-canary') console.log(`KISO OBSERVER_TICK ${config.failStop ? 1 : 0} ${++ticks}`);
    },
    on_stop() {
      console.log(`KISO OBSERVER_STOP ${config.failStop ? 'failed' : 'normal'}`);
      // Intentionally do not unsubscribe or stop timers: Core owns cleanup.
      if (config.failStop) throw new Error('KISO_INTENTIONAL_STOP_FAILURE');
    }
  };
})();
