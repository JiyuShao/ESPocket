// Temporary replacement for Hello Runtime's entry, preserving its Root GUI.
// A Native fixture starts/stops the two hidden observer Apps.
(() => {
  const text = 'KISO_PRIVATE_PROBE'; // Synthetic test text only.
  let round = 0;
  let busy = false;
  async function call(operation, params = {}, service = 'SystemCore') {
    const raw = await brookesia.call_service_function_async(
      service, operation, JSON.stringify(params));
    const result = JSON.parse(raw);
    if (!result.success) throw new Error(result.error);
    return result.data;
  }
  async function pulse() {
    const outputs = await call('GetOutputs', {}, 'Display');
    const output = outputs.find(value => value.name === 'Output0');
    if (!output) throw new Error('display_output_missing');
    const params = {OutputId: output.id};
    const original = await call('GetBacklightBrightness', params, 'Display');
    try {
      await call('SetBacklightBrightness', {...params, Brightness: original === 100 ? 99 : original + 1}, 'Display');
    } finally {
      await call('SetBacklightBrightness', {...params, Brightness: original}, 'Display');
    }
  }
  globalThis.brookesia_app = {
    on_start() {
      brookesia.subscribe_service_event('SystemCore', 'KeyboardClosed');
      brookesia.subscribe_service_event('Display', 'BacklightBrightnessChanged');
      brookesia.call_service_function('SystemGui', 'SubscribeAction',
        JSON.stringify({Action: 'open_detail'}));
      brookesia.call_service_function('SystemTimer', 'StartPeriodic',
        JSON.stringify({Name: 'isolation-pump', IntervalMs: 50}));
      console.log('KISO OWNER_READY');
    },
    on_timer() {}, // Drain actual JS Promise completions without synthetic APIs.
    async on_action(action) {
      if (action !== 'open_detail' || busy) return;
      busy = true;
      try {
        await pulse();
        if (round >= 2) { busy = false; console.log('KISO POST_STOP_PUBLIC_DONE'); return; }
        await call('ShowKeyboard', {Options: {title: 'Isolation fixture', initial_text: text}});
        console.log(`KISO KEYBOARD_OPEN ${round}`);
      } catch (error) { console.log(`KISO FIXTURE_ERROR ${error}`); }
    },
    async on_event(service, event, payload) {
      if (service === 'Display' && event === 'BacklightBrightnessChanged') { console.log('KISO OWNER_PUBLIC_EVENT'); return; }
      if (service !== 'SystemCore' || event !== 'KeyboardClosed') return;
      try {
        const result = JSON.parse(payload);
        if (!result.Confirmed || result.Text !== text) throw new Error('owner_result_mismatch');
        console.log(`KISO OWNER_RESULT ${round}`);
        // The Native fixture coordinates other Apps; Runtime has no such right.
        ++round;
        busy = false;
      } catch (error) { console.log(`KISO FIXTURE_ERROR ${error}`); }
    },
    on_stop() { console.log('KISO OWNER_STOP'); }
  };
})();
