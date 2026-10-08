"""Exercise real App navigation and revoke completions across stop/restart."""
from pathlib import Path
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]


class ChatNavigationTest(unittest.TestCase):
    def test_page_actions_back_and_stale_completions(self):
        script = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const source = fs.readFileSync(process.argv[1], 'utf8').replace(/^import[^\n]+\n/, '');
const requests = [], effects = [];
let stack = ['ai_chatbot_chat'], fail = false, pending;
const context = vm.createContext({
  console, createI18nBundle: () => ({}), brookesia: {print: () => {}},
  espocketNavigation: {dispatch: async text => {
    const request = JSON.parse(text); requests.push(request);
    if (fail) throw Error('presentation_failed');
    if (pending) return new Promise(resolve => { pending.resolve = resolve; });
    if (request.operation === 'push') stack.push(request.pageId);
    if (request.operation === 'requestBack') stack.pop();
    if (request.operation === 'resetToRoot') stack = stack.slice(0, 1);
    return JSON.stringify({pageId: stack.at(-1)});
  }}
});
vm.runInContext(source, context);
for (const name of ['cancelLatestHistoryScroll', 'suspendAgentIfStarted', 'hideErrorDialogIfVisible',
 'resumeAgentIfSuspended', 'renderMissingHistory', 'maybeStartAgent', 'refreshUi',
 'scheduleLatestHistoryScroll', 'populateAgentOptions', 'stopTimer', 'stopAgent',
 'clearHistory', 'clearAgentOptions', 'stopSupportServices']) {
 context[name] = () => effects.push(name);
}
context.navigationAlive = true; context.navigationEpoch = 1;
(async () => {
 await context.openSettingsPage('unused');
 assert.equal(context.currentPage, context.PAGE_SETTINGS);
 await context.openAgentSelectPage('unused');
 assert.deepEqual(stack, ['ai_chatbot_chat','ai_chatbot_settings','ai_chatbot_select']);
 await context.openSettingsPage('unused');
 assert.equal(requests.at(-1).operation, 'requestBack');
 assert.equal(context.currentPage, context.PAGE_SETTINGS);
 // System edge Back changes the real stack; the App reconciles business state.
 stack.pop(); effects.length = 0;
 await context.pollNavigation();
 assert.equal(context.currentPage, context.PAGE_CHAT);
 assert(effects.includes('resumeAgentIfSuspended'));
 await context.openSettingsPage('unused');
 await context.openAgentSelectPage('unused');
 await context.openChatPage('unused');
 assert.deepEqual(stack, ['ai_chatbot_chat']);
 // Repeated root/settings taps never add duplicate pages.
 await context.openChatPage('unused');
 await context.openSettingsPage('unused'); await context.openSettingsPage('unused');
 assert.deepEqual(stack, ['ai_chatbot_chat','ai_chatbot_settings']);
 fail = true; const previous = context.currentPage;
 await context.openAgentSelectPage('unused');
 assert.equal(context.currentPage, previous); fail = false;
 // A pending observer must neither drop a user action nor restore an old page.
 pending = {};
 const observer = context.pollNavigation();
 const oldObserver = pending; pending = null;
 await context.openAgentSelectPage('unused');
 assert.equal(context.currentPage, context.PAGE_AGENT_SELECT);
 oldObserver.resolve(JSON.stringify({pageId: 'ai_chatbot_chat'}));
 await observer; assert.equal(context.currentPage, context.PAGE_AGENT_SELECT);
 // Stop/restart before a pending snapshot resolves must not mutate the new instance.
 pending = {};
 const old = context.pollNavigation();
 context.brookesia_app.on_stop();
 context.navigationAlive = true; ++context.navigationEpoch; context.navigationBusy = false;
 context.currentPage = context.PAGE_CHAT; effects.length = 0;
 pending.resolve(JSON.stringify({pageId: 'ai_chatbot_select'}));
 await old; assert.equal(context.currentPage, context.PAGE_CHAT); assert.equal(effects.length, 0);
 assert(!source.includes('gui("TriggerScreenFlow"'));
})().catch(error => { console.error(error); process.exitCode = 1; });
'''
        subprocess.run(['node', '-e', script, str(APP / 'src/app/chatbot/lifecycle.js')], check=True)


if __name__ == '__main__':
    unittest.main()
