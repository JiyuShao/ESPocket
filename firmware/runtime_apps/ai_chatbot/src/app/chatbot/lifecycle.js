import { createI18nBundle } from "../common/i18n.js";

var coreHandle = 0;
var guiHandle = 0;
var timerHandle = 0;
var deviceHandle = 0;
var agentHandle = 0;
var cozeHandle = 0;
var openaiHandle = 0;
var xiaozhiHandle = 0;
var audioHandle = 0;

var LOG_PREFIX = "[AIChatbot] ";
var SERVICE_TIMEOUT_MS = 1000;
var NETWORK_POLL_INTERVAL_MS = 1000;
var INITIAL_REFRESH_DELAY_MS = 50;
var HISTORY_SCROLL_DELAY_MS = 50;
var ERROR_DIALOG_AUTO_CLOSE_MS = 0;
var MAX_HISTORY_MESSAGES = 10;

var ACTION_CHAT_OPEN_CHAT = "ai_chatbot.chat.open.chat";
var ACTION_CHAT_OPEN_SETTINGS = "ai_chatbot.chat.open.settings";
var ACTION_SETTINGS_OPEN_CHAT = "ai_chatbot.settings.open.chat";
var ACTION_SETTINGS_OPEN_SETTINGS = "ai_chatbot.settings.open.settings";
var ACTION_SETTINGS_OPEN_AGENT_SELECT = "ai_chatbot.settings.open.agent_select";
var ACTION_SELECT_BACK = "ai_chatbot.select.back";
var ACTION_SELECT_BACK_SETTINGS = "ai_chatbot.select.back.settings";
var ACTION_SELECT_AGENT = "ai_chatbot.agent.select";
var ACTION_CLEAR_HISTORY = "ai_chatbot.history.clear";

var NETWORK_TIMER_NAME = "ai_chatbot.network.poll";
var INITIAL_REFRESH_TIMER_NAME = "ai_chatbot.initial.refresh";
var HISTORY_SCROLL_TIMER_NAME = "ai_chatbot.history.scroll_latest";

var AGENT_TEMPLATE_ID = "menu_item";
var AGENT_LIST_PATH = "/ai_chatbot_select/list_card/list";
var AGENT_EMPTY_STATE_PATH = "/ai_chatbot_select/list_card/empty_state";
var AGENT_EMPTY_MESSAGE_PATH = "/ai_chatbot_select/list_card/empty_state/message";
var CHAT_AGENT_TEMPLATE_ID = "chat_message_agent";
var CHAT_USER_TEMPLATE_ID = "chat_message_user";
var CHAT_LIST_PATH = "/ai_chatbot_chat/content/chat_panel/list/items";
var CHAT_EMPTY_STATE_PATH = "/ai_chatbot_chat/content/empty_state";
var CHAT_PANEL_PATH = "/ai_chatbot_chat/content/chat_panel";
var CHAT_MESSAGE_PATH = "/ai_chatbot_chat/content/empty_state/message";
var CHAT_STATUS_NETWORK_VALUE_PATH = "/ai_chatbot_chat/content/empty_state/status_chip_network/status_value";
var CHAT_STATUS_AGENT_VALUE_PATH = "/ai_chatbot_chat/content/empty_state/status_chip_agent/status_value";
var CHAT_STATUS_CLOUD_VALUE_PATH = "/ai_chatbot_chat/content/empty_state/status_chip_cloud/status_value";
var CHROME_ROOT_PATH = "/ai_chatbot_chrome";
var CHROME_TITLE_PATH = "/ai_chatbot_chrome/title";
var CHROME_STATUS_PATH = "/ai_chatbot_chrome/status";
var CHROME_CLEAR_BUTTON_PATH = "/ai_chatbot_chrome/clear";
var CHROME_NAV_CHAT_PILL_PATH = "/ai_chatbot_chrome/chat";
var CHROME_NAV_CHAT_ICON_PATH = "/ai_chatbot_chrome/chat/icon";
var CHROME_NAV_CHAT_LABEL_PATH = "/ai_chatbot_chrome/chat/label";
var CHROME_NAV_SETTINGS_PILL_PATH = "/ai_chatbot_chrome/settings";
var CHROME_NAV_SETTINGS_ICON_PATH = "/ai_chatbot_chrome/settings/icon";
var CHROME_NAV_SETTINGS_LABEL_PATH = "/ai_chatbot_chrome/settings/label";
var SETTINGS_AGENT_VALUE_PATH = "/ai_chatbot_settings/content/agent/value";
var SETTINGS_STATUS_PATH = "/ai_chatbot_settings/content/status/value";

var NAV_ACTIVE_BG = "#E8362D";
var NAV_ACTIVE_TEXT = "#fafbfc";
var NAV_INACTIVE_BG = "#F8F3F2";
var NAV_INACTIVE_BORDER = "#E4D9D5";
var NAV_INACTIVE_TEXT = "#7a7a7a";

var PAGE_CHAT = "Chat";
var PAGE_SETTINGS = "Settings";
var PAGE_AGENT_SELECT = "AgentSelect";

var SERVICE_AGENT_MANAGER = "AgentManager";
var SERVICE_COZE = "Coze";
var SERVICE_OPENAI = "OpenAI";
var SERVICE_XIAOZHI = "XiaoZhi";

var currentPage = PAGE_CHAT;
var currentLocale = "en";
var deviceReady = false;
var agentReady = false;
var networkReady = false;
var internetReady = false;
var agentStarted = false;
var agentSleeping = false;
var agentWakeSubmitted = false;
var agentStartSubmitted = false;
var agentSuspendedByApp = false;
var agentSuspended = false;
var agentSpeaking = false;
var agentListening = false;
var configErrorLatched = false;
var selectedAgentName = "";
var activationCode = "-";
var networkTimerId = 0;
var initialRefreshTimerId = 0;
var historyScrollTimerId = 0;
var historyScrollAnimated = false;
var errorDialogRequestId = 0;
var serviceEventHandles = [];
var agentAttributes = [];
var agentItems = [];
var history = [];
var nextHistoryItemId = 0;
var networkDetail = localized("network.checking");
var agentState = localized("state.unavailable");
var cloudState = localized("cloud.disconnected");
var statusText = localized("status.starting");

var i18n = createI18nBundle(function (name, params, timeoutMs) {
    return gui(name, params, timeoutMs);
}, "aiChatbot.i18n");
var i18nBundle = {strings: {}, updates: []};

function localized(key, argument) {
    return {
        key: key,
        argument: argument || ""
    };
}

function log(message) {
    try {
        brookesia.print(LOG_PREFIX + message);
    } catch (error) {
        /* Diagnostics only. */
    }
}

function errorText(error) {
    if (error && error.message) {
        return error.message;
    }
    return String(error);
}

function resultError(result) {
    return result.error || result.error_message || "unknown error";
}

function parseResult(raw) {
    if (typeof raw !== "string" || raw.length === 0) {
        return {success: false, error: "empty service result"};
    }
    try {
        return JSON.parse(raw);
    } catch (error) {
        return {success: false, error: "invalid service result: " + errorText(error)};
    }
}

function call(handle, name, params, timeoutMs) {
    try {
        var paramsJson = JSON.stringify(params || {});
        if (timeoutMs === undefined) {
            return parseResult(brookesia.call_function(handle, name, paramsJson));
        }
        return parseResult(brookesia.call_function(handle, name, paramsJson, timeoutMs));
    } catch (error) {
        return {success: false, error: errorText(error)};
    }
}

function callAsync(handle, name, params, timeoutMs) {
    try {
        return brookesia.call_function_async(
            handle,
            name,
            JSON.stringify(params || {}),
            timeoutMs || 0
        ).then(function (raw) {
            return parseResult(raw);
        }).catch(function (error) {
            return {success: false, error: errorText(error)};
        });
    } catch (error) {
        return Promise.resolve({success: false, error: errorText(error)});
    }
}

function startService(name) {
    try {
        return brookesia.start_service(name) || 0;
    } catch (error) {
        log("Failed to start service " + name + ": " + errorText(error));
        return 0;
    }
}

function stopService(handle) {
    if (handle === 0) {
        return;
    }
    try {
        brookesia.stop_service(handle);
    } catch (error) {
        log("Failed to stop service handle " + handle + ": " + errorText(error));
    }
}

function core(name, params, timeoutMs) {
    if (coreHandle === 0) {
        return {success: false, error: "SystemCore service is not running"};
    }
    return call(coreHandle, name, params, timeoutMs);
}

function gui(name, params, timeoutMs) {
    if (guiHandle === 0) {
        return {success: false, error: "SystemGui service is not running"};
    }
    return call(guiHandle, name, params, timeoutMs);
}

function timer(name, params, timeoutMs) {
    if (timerHandle === 0) {
        return {success: false, error: "SystemTimer service is not running"};
    }
    return call(timerHandle, name, params, timeoutMs);
}

function device(name, params, timeoutMs) {
    if (deviceHandle === 0) {
        return {success: false, error: "Device service is not running"};
    }
    return call(deviceHandle, name, params, timeoutMs);
}

function agent(name, params, timeoutMs) {
    if (agentHandle === 0) {
        return {success: false, error: "AgentManager service is not running"};
    }
    return call(agentHandle, name, params, timeoutMs);
}

function audio(name, params, timeoutMs) {
    if (audioHandle === 0) {
        return {success: false, error: "AudioPlayback service is not running"};
    }
    return call(audioHandle, name, params, timeoutMs);
}

function firstDefined(values) {
    for (var i = 0; i < values.length; ++i) {
        if (values[i] !== undefined && values[i] !== null) {
            return values[i];
        }
    }
    return undefined;
}

function normalizeBool(value) {
    if (value === true || value === false) {
        return value;
    }
    var text = String(value || "").toLowerCase();
    return text === "true" || text === "1" || text === "yes";
}

function boolValue(value) {
    return value ? "true" : "false";
}

function bindingUpdate(path, key, value) {
    return {
        Path: path,
        Key: key,
        Value: String(value)
    };
}

var appliedBindings = {};

function setBindings(updates, context) {
    updates = updates.filter(function (update) {
        return appliedBindings[update.Path + "\u0000" + update.Key] !== update.Value;
    });
    if (updates.length === 0) {
        return {success: true};
    }
    var result = gui("ExecuteBatch", {
        Commands: [
            {
                Name: "SetBindings",
                Params: {
                    Updates: updates
                }
            }
        ]
    });
    if (!result.success) {
        log((context || "SetBindings") + " failed: " + resultError(result));
    } else {
        updates.forEach(function (update) {
            appliedBindings[update.Path + "\u0000" + update.Key] = update.Value;
        });
    }
    return result;
}

function setText(path, text) {
    return gui("SetText", {
        Path: path,
        Text: String(text)
    });
}

function createView(templateId, parentPath, instanceId) {
    return gui("CreateView", {
        TemplateId: templateId,
        ParentPath: parentPath,
        InstanceId: instanceId
    });
}

function destroyView(path) {
    return gui("DestroyView", {Path: path});
}

function subscribeAction(action) {
    var result = gui("SubscribeAction", {Action: action});
    if (!result.success) {
        log("SubscribeAction failed: " + action + ": " + resultError(result));
    }
}

function subscribeEvent(handle, eventName) {
    if (handle === 0) {
        return 0;
    }
    try {
        return brookesia.subscribe_event(handle, eventName) || 0;
    } catch (error) {
        log("Subscribe event failed: " + eventName + ": " + errorText(error));
        return 0;
    }
}

function subscribeServiceEvent(serviceName, eventName) {
    try {
        return brookesia.subscribe_service_event(serviceName, eventName) || 0;
    } catch (error) {
        log("Subscribe service event failed: " + serviceName + "." + eventName + ": " + errorText(error));
        return 0;
    }
}

function unsubscribeEvent(handle) {
    if (handle === 0) {
        return;
    }
    try {
        brookesia.unsubscribe_event(handle);
    } catch (error) {
        log("Unsubscribe event failed: " + errorText(error));
    }
}

function startDelayedTimer(name, delayMs) {
    var result = timer("StartDelayed", {
        Name: name,
        DelayMs: delayMs
    });
    if (!result.success) {
        log("StartDelayed failed: " + name + ": " + resultError(result));
        return 0;
    }
    return parseInt(result.data, 10) || 0;
}

function startPeriodicTimer(name, intervalMs) {
    var result = timer("StartPeriodic", {
        Name: name,
        IntervalMs: intervalMs
    });
    if (!result.success) {
        log("StartPeriodic failed: " + name + ": " + resultError(result));
        return 0;
    }
    return parseInt(result.data, 10) || 0;
}

function stopTimer(timerId) {
    if (timerId === 0 || timerHandle === 0) {
        return;
    }
    timer("Stop", {TimerId: timerId});
}

function storageLocation(kind, relativePath, volumeId) {
    return {
        Kind: kind,
        RelativePath: relativePath || "",
        VolumeId: volumeId || ""
    };
}

function storageUrl(kind, relativePath, volumeId) {
    return {
        "$brookesiaStorageUrl": storageLocation(kind, relativePath, volumeId)
    };
}

function storageRead(kind, relativePath, volumeId) {
    return core("StorageRead", {
        Location: storageLocation(kind, relativePath, volumeId)
    }, SERVICE_TIMEOUT_MS);
}

function joinPath(parent, child) {
    if (parent.length > 0 && parent.charAt(parent.length - 1) === "/") {
        return parent + child;
    }
    return parent + "/" + child;
}

function makeInstanceId(prefix, index) {
    return prefix + "_" + String(index);
}

function extractChildInstanceId(parent, path) {
    if (String(path || "").indexOf(parent) !== 0) {
        return "";
    }
    var instanceId = String(path || "").slice(parent.length);
    if (instanceId.charAt(0) === "/") {
        instanceId = instanceId.slice(1);
    }
    var slash = instanceId.indexOf("/");
    if (slash >= 0) {
        instanceId = instanceId.slice(0, slash);
    }
    return instanceId;
}

function isTextBlank(text) {
    return String(text || "").replace(/\s+/g, "").length === 0;
}

function formatText(text, argument) {
    return String(text).replace("{0}", argument || "");
}

function tr(key, argument) {
    var strings = i18nBundle.strings || {};
    var value = strings[key] || key;
    if (argument !== undefined && argument !== null && String(argument).length > 0) {
        return formatText(value, String(argument));
    }
    return value;
}

function localizedText(value) {
    return tr(value.key, value.argument);
}

function currentLanguage() {
    var result = core("GetEnvironment", {}, SERVICE_TIMEOUT_MS);
    if (result.success && result.data) {
        var language = firstDefined([result.data.language, result.data.Language]);
        if (typeof language === "string" && language.length > 0) {
            return language;
        }
    }
    return "en";
}

function applyLocale() {
    currentLocale = currentLanguage();
    i18nBundle = i18n.load();
    var updates = [];
    var rawUpdates = i18nBundle.updates || [];
    for (var i = 0; i < rawUpdates.length; ++i) {
        var item = rawUpdates[i] || {};
        var path = item.path || item.Path || item[0];
        var key = item.key || item.Key || item[1];
        var value = item.value || item.Value || item[2];
        if (path && key && value !== undefined) {
            updates.push(bindingUpdate(path, key, value));
        }
    }
    setBindings(updates, "Apply locale");
}

function addBinding(updates, path, key, value) {
    updates.push(bindingUpdate(path, key, value));
}

function agentName(attributes) {
    if (!attributes) {
        return "";
    }
    return String(firstDefined([attributes.name, attributes.Name]) || "");
}

function selectedAgentLabel() {
    return selectedAgentName.length > 0 ? selectedAgentName : tr("app.name");
}

function selectedAgentAttributes() {
    for (var i = 0; i < agentAttributes.length; ++i) {
        if (agentName(agentAttributes[i]) === selectedAgentName) {
            return agentAttributes[i];
        }
    }
    return null;
}

function listContainsText(list, expected) {
    if (!list || typeof list.length !== "number") {
        return false;
    }
    for (var i = 0; i < list.length; ++i) {
        if (String(list[i]) === expected) {
            return true;
        }
    }
    return false;
}

function selectedAgentSupportsChat() {
    var attributes = selectedAgentAttributes();
    if (!attributes) {
        return false;
    }
    var events = firstDefined([
        attributes.support_general_events,
        attributes.supportGeneralEvents,
        attributes.SupportGeneralEvents
    ]) || [];
    return listContainsText(events, "AgentSpeakingTextGot") || listContainsText(events, "UserSpeakingTextGot");
}

function selectedAgentConfigFile() {
    if (selectedAgentName === SERVICE_COZE) {
        return "coze.json";
    }
    if (selectedAgentName === SERVICE_OPENAI) {
        return "openai.json";
    }
    return "";
}

function setNetworkDetail(key, argument) {
    networkDetail = localized(key, argument);
}

function setAgentState(key, argument) {
    agentState = localized(key, argument);
}

function setCloudState(key, argument) {
    cloudState = localized(key, argument);
}

function setStatus(key, argument) {
    statusText = localized(key, argument);
}

function composeHeaderStatus() {
    if (!networkReady || !internetReady) {
        return localizedText(networkDetail);
    }
    if (!agentReady) {
        return tr("status.agent_manager_unavailable");
    }
    if (agentSuspended) {
        return tr("state.suspended");
    }
    if (agentSpeaking && agentListening) {
        return tr("status.listening_while_speaking");
    }
    if (agentSpeaking) {
        return tr("status.agent_speaking");
    }
    if (agentListening) {
        return tr("status.listening");
    }
    if (agentSleeping) {
        return tr("status.agent_sleeping");
    }
    if (agentStarted) {
        return selectedAgentSupportsChat() ? tr("status.chat_ready") : tr("state.started");
    }
    return localizedText(statusText);
}

function refreshUi() {
    if (coreHandle !== 0) {
        var language = currentLanguage();
        if (language !== currentLocale) {
            applyLocale();
        }
    }

    var agentValue = selectedAgentName.length === 0 ? tr("state.unavailable") : selectedAgentName;
    var showChat = agentStarted && selectedAgentSupportsChat();
    var showChrome = currentPage !== PAGE_AGENT_SELECT;
    var chatActive = currentPage === PAGE_CHAT;
    var agentSelectEmpty = agentAttributes.length === 0;
    var updates = [];
    var networkText = localizedText(networkDetail);
    var agentText = localizedText(agentState);
    var cloudText = localizedText(cloudState);
    addBinding(updates, CHROME_ROOT_PATH, "commonProps.hidden", boolValue(!showChrome));
    if (showChrome) {
        addBinding(updates, CHROME_TITLE_PATH, "labelProps.text", tr("app.name"));
        addBinding(updates, CHROME_STATUS_PATH, "labelProps.text", composeHeaderStatus());
        addBinding(updates, CHROME_CLEAR_BUTTON_PATH, "commonProps.hidden", boolValue(!chatActive || history.length === 0));
        addBinding(updates, CHROME_NAV_CHAT_PILL_PATH, "style.bgColor", chatActive ? NAV_ACTIVE_BG : NAV_INACTIVE_BG);
        addBinding(updates, CHROME_NAV_CHAT_PILL_PATH, "style.borderColor", chatActive ? NAV_ACTIVE_BG : NAV_INACTIVE_BORDER);
        addBinding(updates, CHROME_NAV_CHAT_PILL_PATH, "style.borderWidth", chatActive ? "0dp" : "1dp");
        addBinding(updates, CHROME_NAV_CHAT_LABEL_PATH, "style.textColor", chatActive ? NAV_ACTIVE_TEXT : NAV_INACTIVE_TEXT);
        addBinding(updates, CHROME_NAV_CHAT_ICON_PATH, "style.imageRecolor", chatActive ? NAV_ACTIVE_TEXT : NAV_INACTIVE_TEXT);
        addBinding(updates, CHROME_NAV_CHAT_ICON_PATH, "style.imageRecolorOpacity", "255");
        addBinding(updates, CHROME_NAV_SETTINGS_PILL_PATH, "style.bgColor", chatActive ? NAV_INACTIVE_BG : NAV_ACTIVE_BG);
        addBinding(updates, CHROME_NAV_SETTINGS_PILL_PATH, "style.borderColor", chatActive ? NAV_INACTIVE_BORDER : NAV_ACTIVE_BG);
        addBinding(updates, CHROME_NAV_SETTINGS_PILL_PATH, "style.borderWidth", chatActive ? "1dp" : "0dp");
        addBinding(updates, CHROME_NAV_SETTINGS_LABEL_PATH, "style.textColor", chatActive ? NAV_INACTIVE_TEXT : NAV_ACTIVE_TEXT);
        addBinding(updates, CHROME_NAV_SETTINGS_ICON_PATH, "style.imageRecolor", chatActive ? NAV_INACTIVE_TEXT : NAV_ACTIVE_TEXT);
        addBinding(updates, CHROME_NAV_SETTINGS_ICON_PATH, "style.imageRecolorOpacity", "255");
    }

    if (currentPage === PAGE_CHAT) {
        addBinding(updates, CHAT_STATUS_NETWORK_VALUE_PATH, "labelProps.text", networkText);
        addBinding(updates, CHAT_STATUS_AGENT_VALUE_PATH, "labelProps.text", agentText);
        addBinding(updates, CHAT_STATUS_CLOUD_VALUE_PATH, "labelProps.text", cloudText);
        addBinding(updates, CHAT_MESSAGE_PATH, "labelProps.text", localizedText(statusText));
        addBinding(updates, CHAT_EMPTY_STATE_PATH, "commonProps.hidden", boolValue(showChat));
        addBinding(updates, CHAT_PANEL_PATH, "commonProps.hidden", boolValue(!showChat));
    } else if (currentPage === PAGE_SETTINGS) {
        addBinding(updates, SETTINGS_AGENT_VALUE_PATH, "labelProps.text", agentValue);
        addBinding(updates, SETTINGS_STATUS_PATH, "labelProps.text", localizedText(statusText));
    } else if (currentPage === PAGE_AGENT_SELECT) {
        addBinding(updates, AGENT_EMPTY_STATE_PATH, "commonProps.hidden", boolValue(!agentSelectEmpty));
        addBinding(updates, AGENT_EMPTY_MESSAGE_PATH, "labelProps.text", localizedText(statusText));
        addBinding(updates, AGENT_LIST_PATH, "commonProps.hidden", boolValue(agentSelectEmpty));
    }

    setBindings(updates, "Refresh UI");
}

function subscribeActions() {
    var actions = [
        ACTION_CHAT_OPEN_CHAT,
        ACTION_CHAT_OPEN_SETTINGS,
        ACTION_SETTINGS_OPEN_CHAT,
        ACTION_SETTINGS_OPEN_SETTINGS,
        ACTION_SETTINGS_OPEN_AGENT_SELECT,
        ACTION_SELECT_BACK,
        ACTION_SELECT_BACK_SETTINGS,
        ACTION_CLEAR_HISTORY,
        ACTION_SELECT_AGENT
    ];
    for (var i = 0; i < actions.length; ++i) {
        subscribeAction(actions[i]);
    }
}

function bindServices() {
    deviceReady = false;
    agentReady = false;
    deviceHandle = startService("Device");
    agentHandle = startService(SERVICE_AGENT_MANAGER);
    audioHandle = startService("AudioPlayback");
    deviceReady = deviceHandle !== 0;
    agentReady = agentHandle !== 0;
    if (!deviceReady) {
        setStatus("status.device_service_unavailable");
    }
    if (!agentReady) {
        setAgentState("state.unavailable");
        setStatus("status.agent_manager_unavailable");
    }
}

function releaseServices() {
    stopService(audioHandle);
    stopService(xiaozhiHandle);
    stopService(openaiHandle);
    stopService(cozeHandle);
    stopService(agentHandle);
    stopService(deviceHandle);
    audioHandle = 0;
    xiaozhiHandle = 0;
    openaiHandle = 0;
    cozeHandle = 0;
    agentHandle = 0;
    deviceHandle = 0;
    agentReady = false;
    deviceReady = false;
}

function disconnectAgentEvents() {
    for (var i = 0; i < serviceEventHandles.length; ++i) {
        unsubscribeEvent(serviceEventHandles[i]);
    }
    serviceEventHandles = [];
}

function subscribeAgentEvents() {
    disconnectAgentEvents();
    if (!agentReady) {
        return;
    }
    var agentEvents = [
        "GeneralActionTriggered",
        "GeneralEventHappened",
        "SuspendStatusChanged",
        "SpeakingStatusChanged",
        "ListeningStatusChanged",
        "AgentSpeakingTextGot",
        "UserSpeakingTextGot"
    ];
    for (var i = 0; i < agentEvents.length; ++i) {
        var handle = subscribeEvent(agentHandle, agentEvents[i]);
        if (handle !== 0) {
            serviceEventHandles.push(handle);
        }
    }
    var xiaozhiEvent = subscribeServiceEvent(SERVICE_XIAOZHI, "ActivationCodeReceived");
    if (xiaozhiEvent !== 0) {
        serviceEventHandles.push(xiaozhiEvent);
    }
    var cozeEvent = subscribeServiceEvent(SERVICE_COZE, "CozeEventHappened");
    if (cozeEvent !== 0) {
        serviceEventHandles.push(cozeEvent);
    }
}

function loadAgentsAndTarget() {
    agentAttributes = [];
    selectedAgentName = "";
    if (!agentReady) {
        setStatus("status.agent_manager_unavailable");
        return false;
    }

    var attrsResult = agent("GetAgentAttributes", {Name: ""}, SERVICE_TIMEOUT_MS);
    if (!attrsResult.success || !attrsResult.data || typeof attrsResult.data.length !== "number") {
        setStatus("status.get_agent_list_failed", resultError(attrsResult));
        return false;
    }
    agentAttributes = attrsResult.data;

    var targetResult = agent("GetTargetAgent", {}, SERVICE_TIMEOUT_MS);
    if (targetResult.success && typeof targetResult.data === "string") {
        selectedAgentName = targetResult.data;
    } else if (!targetResult.success) {
        log("GetTargetAgent failed: " + resultError(targetResult));
    }

    if (!selectedAgentAttributes() && agentAttributes.length > 0) {
        selectedAgentName = agentName(agentAttributes[0]);
        var fallback = agent("SetTargetAgent", {Name: selectedAgentName}, SERVICE_TIMEOUT_MS);
        if (!fallback.success) {
            setStatus("status.set_fallback_failed", resultError(fallback));
            return false;
        }
    }

    if (selectedAgentName.length === 0) {
        setStatus("status.no_agent_available");
        setAgentState("state.no_agent");
    } else {
        setStatus("status.selected_agent", selectedAgentLabel());
        setAgentState("state.selected");
    }
    if (currentPage === PAGE_AGENT_SELECT) {
        populateAgentOptions();
    }
    return true;
}

function clearAgentOptions() {
    for (var i = agentItems.length - 1; i >= 0; --i) {
        destroyView(agentItems[i].viewPath);
    }
    agentItems = [];
}

function populateAgentOptions() {
    clearAgentOptions();
    if (agentAttributes.length === 0) {
        setStatus("status.no_agent_available");
        refreshUi();
        return false;
    }
    for (var i = 0; i < agentAttributes.length; ++i) {
        var name = agentName(agentAttributes[i]);
        var instanceId = makeInstanceId("agent", i);
        var path = joinPath(AGENT_LIST_PATH, instanceId);
        var created = createView(AGENT_TEMPLATE_ID, AGENT_LIST_PATH, instanceId);
        if (!created.success) {
            log("Create agent option failed: " + resultError(created));
            clearAgentOptions();
            return false;
        }
        agentItems.push({
            instanceId: instanceId,
            viewPath: path,
            name: name
        });
        setBindings([
            bindingUpdate(joinPath(path, "title"), "labelProps.text", name),
            bindingUpdate(joinPath(path, "value"), "labelProps.text", name === selectedAgentName ? tr("text.current") : "")
        ], "Populate agent option");
    }
    refreshUi();
    return true;
}

function handleAgentSelectPath(path) {
    var instanceId = extractChildInstanceId(AGENT_LIST_PATH, path);
    for (var i = 0; i < agentItems.length; ++i) {
        if (agentItems[i].instanceId === instanceId) {
            selectAgent(agentItems[i].name);
            openSettingsPage(ACTION_SELECT_BACK);
            return;
        }
    }
    log("Ignore selection from unknown path: " + String(path || ""));
}

function selectAgent(name) {
    if (!agentReady) {
        return false;
    }
    var setTarget = agent("SetTargetAgent", {Name: name}, SERVICE_TIMEOUT_MS);
    if (!setTarget.success) {
        setStatus("status.set_target_failed", resultError(setTarget));
        refreshUi();
        return false;
    }
    if (agentStarted || agentStartSubmitted) {
        stopAgent();
    }
    selectedAgentName = String(name || "");
    agentStarted = false;
    agentSleeping = false;
    agentWakeSubmitted = false;
    agentStartSubmitted = false;
    agentSuspendedByApp = false;
    agentSuspended = false;
    agentSpeaking = false;
    agentListening = false;
    configErrorLatched = false;
    setCloudState("cloud.disconnected");
    setAgentState("state.selected");
    activationCode = "-";
    clearHistory();
    hideErrorDialogIfVisible();
    setStatus("status.selected_agent", selectedAgentLabel());
    populateAgentOptions();
    return true;
}

function renderMissingHistory() {
    for (var i = 0; i < history.length; ++i) {
        var message = history[i];
        if (message.itemPath.length > 0) {
            continue;
        }
        var instanceId = "message_" + String(nextHistoryItemId++);
        var templateId = message.speaker === "User" ? CHAT_USER_TEMPLATE_ID : CHAT_AGENT_TEMPLATE_ID;
        var path = joinPath(CHAT_LIST_PATH, instanceId);
        var created = createView(templateId, CHAT_LIST_PATH, instanceId);
        if (!created.success) {
            log("Create history item failed: " + resultError(created));
            return false;
        }
        message.itemPath = path;
        var textResult = setText(joinPath(path, "bubble/text"), message.text);
        if (!textResult.success) {
            log("Set history text failed: " + resultError(textResult));
            return false;
        }
    }
    return true;
}

function scrollLatestHistoryIntoView(animated) {
    if (currentPage !== PAGE_CHAT || !agentStarted || !selectedAgentSupportsChat() || history.length === 0) {
        return;
    }
    var path = history[history.length - 1].itemPath;
    if (path.length === 0) {
        return;
    }
    var result = gui("ExecuteBatch", {
        Commands: [
            {
                Name: "ScrollToView",
                Params: {
                    Path: path,
                    Animated: animated === true
                }
            }
        ]
    });
    if (!result.success) {
        log("Scroll history failed: " + resultError(result));
    }
}

function scheduleLatestHistoryScroll(animated) {
    if (timerHandle === 0 || currentPage !== PAGE_CHAT || history.length === 0) {
        return;
    }
    historyScrollAnimated = historyScrollAnimated || animated;
    if (historyScrollTimerId !== 0) {
        stopTimer(historyScrollTimerId);
        historyScrollTimerId = 0;
    }
    historyScrollTimerId = startDelayedTimer(HISTORY_SCROLL_TIMER_NAME, HISTORY_SCROLL_DELAY_MS);
    if (historyScrollTimerId === 0) {
        scrollLatestHistoryIntoView(historyScrollAnimated);
        historyScrollAnimated = false;
    }
}

function cancelLatestHistoryScroll() {
    if (historyScrollTimerId !== 0) {
        stopTimer(historyScrollTimerId);
    }
    historyScrollTimerId = 0;
    historyScrollAnimated = false;
}

function clearHistory() {
    cancelLatestHistoryScroll();
    for (var i = 0; i < history.length; ++i) {
        if (history[i].itemPath.length > 0) {
            destroyView(history[i].itemPath);
        }
    }
    history = [];
    nextHistoryItemId = 0;
}

function appendHistory(speaker, text) {
    if (!selectedAgentSupportsChat()) {
        return;
    }
    history.push({
        speaker: speaker,
        text: String(text || ""),
        itemPath: ""
    });
    while (history.length > MAX_HISTORY_MESSAGES) {
        if (history[0].itemPath.length > 0) {
            destroyView(history[0].itemPath);
        }
        history.shift();
    }
    renderMissingHistory();
    refreshUi();
    scheduleLatestHistoryScroll(true);
}

function parseNetworkReady(data) {
    if (!data || typeof data.length !== "number") {
        networkReady = false;
        return "network.info_parse_failed";
    }
    var localReady = false;
    var cloudReady = false;
    for (var i = 0; i < data.length; ++i) {
        var item = data[i] || {};
        var ready = normalizeBool(firstDefined([item.network_ready, item.networkReady, item.NetworkReady]));
        localReady = localReady || ready;
        cloudReady = cloudReady || ready;
    }
    networkReady = localReady;
    if (cloudReady) {
        return "network.internet_ready";
    }
    if (localReady) {
        return "network.local_ready";
    }
    return "network.waiting";
}

function pollNetworkAndMaybeStart() {
    if (internetReady) {
        maybeStartAgent();
        refreshUi();
        return;
    }
    if (!deviceReady) {
        setNetworkDetail("network.device_unavailable");
        refreshUi();
        return;
    }
    var result = device("GetNetworkConnectivityInfo", {}, SERVICE_TIMEOUT_MS);
    if (!result.success) {
        setNetworkDetail("network.check_failed", resultError(result));
        internetReady = false;
        networkReady = false;
        refreshUi();
        return;
    }
    var detail = parseNetworkReady(result.data);
    setNetworkDetail(detail);
    internetReady = detail === "network.internet_ready";
    if (internetReady && networkTimerId !== 0) {
        stopTimer(networkTimerId);
        networkTimerId = 0;
    }
    if (internetReady) {
        maybeStartAgent();
    }
    refreshUi();
}

function readJsonConfig(fileName) {
    var result = storageRead("AppData", fileName);
    if (!result.success) {
        return {success: false, error: "Config file not found: " + fileName + ": " + resultError(result)};
    }
    if (isTextBlank(result.data)) {
        return {success: false, error: "Config file is empty: " + fileName};
    }
    try {
        var parsed = JSON.parse(result.data);
        if (!parsed || typeof parsed !== "object" || typeof parsed.length === "number") {
            return {success: false, error: "Config JSON root must be an object: " + fileName};
        }
        return {success: true, data: parsed};
    } catch (error) {
        return {success: false, error: "Config JSON parse failed: " + fileName + ": " + errorText(error)};
    }
}

function requireNonEmpty(value, name) {
    if (isTextBlank(value)) {
        return name + " is empty";
    }
    return "";
}

function validateOpenaiConfig(config) {
    var error = requireNonEmpty(config && config.model, "OpenAI model");
    if (error.length > 0) {
        return {success: false, error: error};
    }
    error = requireNonEmpty(config && config.api_key, "OpenAI api_key");
    if (error.length > 0) {
        return {success: false, error: error};
    }
    return {success: true, data: config};
}

function validateCozeConfig(config) {
    var authorization = config && config.authorization;
    if (!authorization || typeof authorization !== "object") {
        return {success: false, error: "Coze authorization must be an object"};
    }
    if (isTextBlank(authorization.private_key)) {
        var privateKey = storageRead("AppData", "coze_private_key.pem");
        if (privateKey.success && !isTextBlank(privateKey.data)) {
            authorization.private_key = privateKey.data;
        }
    }
    var error = requireNonEmpty(authorization.app_id, "Coze authorization.app_id");
    if (error.length > 0) {
        return {success: false, error: error};
    }
    error = requireNonEmpty(authorization.public_key, "Coze authorization.public_key");
    if (error.length > 0) {
        return {success: false, error: error};
    }
    error = requireNonEmpty(authorization.private_key, "Coze authorization.private_key");
    if (error.length > 0) {
        return {success: false, error: error + " (set it in coze.json or coze_private_key.pem)"};
    }
    if (!config.robots || typeof config.robots.length !== "number" || config.robots.length === 0) {
        return {success: false, error: "Coze robots is empty"};
    }
    for (var i = 0; i < config.robots.length; ++i) {
        var robot = config.robots[i] || {};
        if (isTextBlank(robot.name) || isTextBlank(robot.bot_id) || isTextBlank(robot.voice_id)) {
            return {success: false, error: "Coze robot[" + String(i) + "] requires name, bot_id, and voice_id"};
        }
    }
    return {success: true, data: config};
}

function loadSelectedAgentConfig() {
    var configFile = selectedAgentConfigFile();
    if (configFile.length === 0) {
        return {success: false, error: "Selected agent does not require a config file"};
    }
    var config = readJsonConfig(configFile);
    if (!config.success) {
        return config;
    }
    if (selectedAgentName === SERVICE_COZE) {
        return validateCozeConfig(config.data);
    }
    if (selectedAgentName === SERVICE_OPENAI) {
        return validateOpenaiConfig(config.data);
    }
    return {success: false, error: "Selected agent does not require a config file"};
}

function showErrorDialog(title, detail) {
    if (coreHandle === 0) {
        return;
    }
    var options = {
        text: title,
        informativeText: detail,
        icon: "Warning",
        buttons: [
            {text: tr("button.ok"), role: "Accept"}
        ],
        autoCloseMs: ERROR_DIALOG_AUTO_CLOSE_MS
    };
    var result;
    if (errorDialogRequestId !== 0) {
        result = core("UpdateMessageDialog", {
            RequestId: errorDialogRequestId,
            Options: options
        }, SERVICE_TIMEOUT_MS);
        if (result.success) {
            return;
        }
        errorDialogRequestId = 0;
    }
    result = core("ShowMessageDialog", {Options: options}, SERVICE_TIMEOUT_MS);
    if (!result.success) {
        log("Show error dialog failed: " + resultError(result));
        return;
    }
    errorDialogRequestId = parseInt(firstDefined([
        result.data && result.data.RequestId,
        result.data && result.data.request_id,
        result.data && result.data.requestId,
        result.data
    ]), 10) || 0;
}

function hideErrorDialogIfVisible() {
    if (errorDialogRequestId === 0 || coreHandle === 0) {
        errorDialogRequestId = 0;
        return;
    }
    core("HideMessageDialog", {RequestId: errorDialogRequestId}, 500);
    errorDialogRequestId = 0;
}

function configureSelectedAgent() {
    if (!agentReady) {
        setStatus("status.agent_manager_unavailable");
        return false;
    }
    if (selectedAgentName.length === 0) {
        setStatus("status.no_agent_selected");
        return false;
    }
    var configFile = selectedAgentConfigFile();
    if (configFile.length > 0) {
        var config = loadSelectedAgentConfig();
        if (!config.success) {
            configErrorLatched = true;
            var detail = tr("label.agent") + ": " + selectedAgentLabel() + "\n" +
                         tr("label.config") + ": " + configFile + "\n" +
                         tr("label.data_dir") + ": AppData\n" +
                         tr("label.reason") + ": " + config.error;
            setStatus("status.config_error", configFile);
            showErrorDialog(tr("dialog.config_error.title"), detail);
            return false;
        }
        hideErrorDialogIfVisible();
        configErrorLatched = false;
        var setInfo = agent("SetAgentInfo", {
            Name: selectedAgentName,
            Info: config.data
        }, SERVICE_TIMEOUT_MS);
        if (!setInfo.success) {
            setStatus("status.set_agent_info_failed", resultError(setInfo));
            return false;
        }
    } else {
        hideErrorDialogIfVisible();
        configErrorLatched = false;
    }
    var target = agent("SetTargetAgent", {Name: selectedAgentName}, SERVICE_TIMEOUT_MS);
    if (!target.success) {
        setStatus("status.set_target_failed", resultError(target));
        return false;
    }
    setStatus("status.configured_agent", selectedAgentLabel());
    return true;
}

function maybeStartAgent() {
    if (currentPage !== PAGE_CHAT) {
        return false;
    }
    if (!internetReady) {
        setStatus("status.waiting_internet");
        return false;
    }
    if (configErrorLatched || agentStartSubmitted || agentStarted) {
        return false;
    }
    if (!configureSelectedAgent()) {
        return false;
    }
    startAgent();
    return true;
}

function triggerAgentActionAsync(actionName, failedStatusKey) {
    callAsync(agentHandle, "TriggerGeneralAction", {Action: actionName}, 0).then(function (result) {
        if (!result.success) {
            setStatus(failedStatusKey, resultError(result));
            agentStartSubmitted = false;
            refreshUi();
        }
    });
}

function startAgent() {
    if (!internetReady) {
        setStatus("status.waiting_internet");
        return;
    }
    if (!agentReady) {
        setStatus("status.agent_manager_unavailable");
        return;
    }
    agentStartSubmitted = true;
    setStatus("status.starting_agent", selectedAgentLabel());
    triggerAgentActionAsync("Activate", "status.activate_failed");
    triggerAgentActionAsync("Start", "status.start_failed");
    refreshUi();
}

function stopAgent() {
    if (!agentReady) {
        return;
    }
    callAsync(agentHandle, "TriggerGeneralAction", {Action: "Stop"}, 0);
    agentStarted = false;
    agentSleeping = false;
    agentWakeSubmitted = false;
    agentStartSubmitted = false;
    agentSuspendedByApp = false;
    agentSuspended = false;
    agentSpeaking = false;
    agentListening = false;
    setCloudState("cloud.disconnected");
}

function suspendAgentIfStarted() {
    if (!agentReady || !agentStarted || agentSuspendedByApp) {
        return;
    }
    var result = agent("Suspend", {}, SERVICE_TIMEOUT_MS);
    if (!result.success) {
        log("Suspend failed: " + resultError(result));
        return;
    }
    agentSuspendedByApp = true;
    agentSuspended = true;
    setAgentState("state.suspended");
    setStatus("status.agent_suspended");
    refreshUi();
}

function resumeAgentIfSuspended() {
    if (!agentReady || !agentSuspendedByApp) {
        return;
    }
    var result = agent("Resume", {}, SERVICE_TIMEOUT_MS);
    if (!result.success) {
        log("Resume failed: " + resultError(result));
        return;
    }
    agentSuspendedByApp = false;
    agentSuspended = false;
    setAgentState(agentStarted ? "state.started" : "state.selected");
    setStatus(agentStarted ? "status.chat_ready" : "status.selected_agent", selectedAgentLabel());
    refreshUi();
}

function generalActionToState(actionName) {
    if (actionName === "TimeSync") {
        return "state.time_syncing";
    }
    if (actionName === "Activate") {
        return "state.activating";
    }
    if (actionName === "Start") {
        return "state.starting";
    }
    if (actionName === "Sleep") {
        return "state.sleeping";
    }
    if (actionName === "WakeUp") {
        return "state.waking";
    }
    if (actionName === "Stop") {
        return "state.stopping";
    }
    return actionName;
}

function generalEventToState(eventName) {
    if (eventName === "TimeSynced") {
        return "state.ready";
    }
    if (eventName === "Activated") {
        return "state.activated";
    }
    if (eventName === "Started") {
        return "state.started";
    }
    if (eventName === "Stopped") {
        return "state.stopped";
    }
    if (eventName === "Slept") {
        return "state.sleeping";
    }
    if (eventName === "Awake") {
        return "state.awake";
    }
    return eventName;
}

function handleGeneralActionTriggered(actionName) {
    setAgentState(generalActionToState(actionName));
    if (actionName === "Activate") {
        setCloudState("cloud.connecting");
        setStatus("status.activating_agent", selectedAgentLabel());
    } else if (actionName === "Start") {
        agentStartSubmitted = true;
        agentSuspended = false;
        agentSuspendedByApp = false;
        setStatus("status.starting_agent", selectedAgentLabel());
    } else if (actionName === "Sleep") {
        agentSpeaking = false;
        agentListening = false;
        setStatus("status.agent_sleeping");
    } else if (actionName === "WakeUp") {
        agentSuspended = false;
        agentSuspendedByApp = false;
        setStatus("status.agent_waking");
    } else if (actionName === "Stop") {
        agentStartSubmitted = false;
        setStatus("status.stopping_agent", selectedAgentLabel());
    } else {
        setStatus(generalActionToState(actionName));
    }
    refreshUi();
}

function handleGeneralEventHappened(eventName, unexpected) {
    setAgentState(generalEventToState(eventName));
    if (unexpected) {
        setStatus("status.unexpected_event", eventName);
    }
    if (eventName === "TimeSynced") {
        setStatus("status.time_synced");
    } else if (eventName === "Activated") {
        setCloudState("cloud.connected");
        setStatus("status.agent_activated");
    } else if (eventName === "Started") {
        agentSleeping = false;
        agentWakeSubmitted = false;
        setCloudState("cloud.connected");
        agentStarted = true;
        agentStartSubmitted = false;
        agentSuspended = false;
        agentSuspendedByApp = false;
        setStatus(selectedAgentSupportsChat() ? "status.chat_ready" : "status.agent_started");
    } else if (eventName === "Awake") {
        agentSleeping = false;
        agentWakeSubmitted = false;
        agentStarted = true;
        agentSuspended = false;
        agentSuspendedByApp = false;
        setStatus(selectedAgentSupportsChat() ? "status.chat_awake" : "status.agent_awake");
    } else if (eventName === "Slept") {
        agentSleeping = true;
        agentWakeSubmitted = false;
        agentSpeaking = false;
        agentListening = false;
        setStatus("status.agent_sleeping");
    } else if (eventName === "Stopped") {
        setCloudState("cloud.disconnected");
        agentStarted = false;
        agentSleeping = false;
        agentWakeSubmitted = false;
        agentStartSubmitted = false;
        agentSuspendedByApp = false;
        agentSuspended = false;
        agentSpeaking = false;
        agentListening = false;
        setStatus("status.stopped");
    }
    refreshUi();
    scheduleLatestHistoryScroll(true);
}

function handleSuspendStatusChanged(suspended) {
    agentSuspended = suspended;
    if (!suspended) {
        agentSuspendedByApp = false;
    }
    if (suspended) {
        setAgentState("state.suspended");
        agentSpeaking = false;
        agentListening = false;
        setStatus("status.agent_suspended");
    } else {
        setAgentState(agentStarted ? "state.started" : "state.selected");
        setStatus(agentStarted ? "status.chat_ready" : "status.selected_agent", selectedAgentLabel());
    }
    refreshUi();
}

function handleSpeakingStatusChanged(speaking) {
    agentSpeaking = speaking;
    if (speaking && agentListening) {
        setStatus("status.listening_while_speaking");
    } else if (speaking) {
        setStatus("status.agent_speaking");
    } else if (agentListening) {
        setStatus("status.listening");
    } else if (agentStarted) {
        setStatus(selectedAgentSupportsChat() ? "status.chat_ready" : "status.agent_started");
    }
    refreshUi();
}

function handleListeningStatusChanged(listening) {
    agentListening = listening;
    if (listening && agentSpeaking) {
        setStatus("status.listening_while_speaking");
    } else if (listening) {
        setStatus("status.listening");
    } else if (agentSpeaking) {
        setStatus("status.agent_speaking");
    } else if (agentStarted) {
        setStatus(selectedAgentSupportsChat() ? "status.chat_ready" : "status.agent_started");
    }
    refreshUi();
}

function playXiaoZhiActivationCode(code) {
    if (audioHandle === 0 || isTextBlank(code)) {
        return;
    }
    var urls = [storageUrl("AppFiles", "xiaozhi/activation.mp3")];
    var text = String(code || "");
    for (var i = 0; i < text.length; ++i) {
        var ch = text.charAt(i);
        if (ch >= "0" && ch <= "9") {
            urls.push(storageUrl("AppFiles", "xiaozhi/" + ch + ".mp3"));
        }
    }
    var result = audio("PlayUrls", {
        Urls: urls,
        Config: {
            interrupt: true,
            delay_ms: 0,
            loop_count: 0,
            loop_interval_ms: 0,
            timeout_ms: 0
        }
    }, SERVICE_TIMEOUT_MS);
    if (!result.success) {
        log("Play XiaoZhi activation audio failed: " + resultError(result));
    }
}

function handleCozeEventHappened(cozeEvent) {
    if (cozeEvent !== "InsufficientCreditsBalance") {
        return;
    }
    setCloudState("cloud.insufficient_credits");
    setStatus("status.coze_insufficient_credits");
    showErrorDialog(tr("dialog.coze_credits.title"), tr("dialog.coze_credits.detail"));
    refreshUi();
}

function handleServiceEvent(serviceName, eventName, itemsJson) {
    var items = {};
    try {
        items = JSON.parse(itemsJson || "{}");
    } catch (error) {
        log("Invalid event payload: " + errorText(error));
        return;
    }

    if (serviceName === SERVICE_AGENT_MANAGER) {
        if (eventName === "GeneralActionTriggered") {
            handleGeneralActionTriggered(String(firstDefined([items.Action, items.action]) || ""));
        } else if (eventName === "GeneralEventHappened") {
            handleGeneralEventHappened(
                String(firstDefined([items.Event, items.event]) || ""),
                normalizeBool(firstDefined([items.IsUnexpected, items.is_unexpected, items.isUnexpected]))
            );
        } else if (eventName === "SuspendStatusChanged") {
            handleSuspendStatusChanged(normalizeBool(firstDefined([items.IsSuspended, items.is_suspended, items.isSuspended])));
        } else if (eventName === "SpeakingStatusChanged") {
            handleSpeakingStatusChanged(normalizeBool(firstDefined([items.IsSpeaking, items.is_speaking, items.isSpeaking])));
        } else if (eventName === "ListeningStatusChanged") {
            handleListeningStatusChanged(normalizeBool(firstDefined([items.IsListening, items.is_listening, items.isListening])));
        } else if (eventName === "UserSpeakingTextGot") {
            appendHistory("User", String(firstDefined([items.Text, items.text]) || ""));
        } else if (eventName === "AgentSpeakingTextGot") {
            appendHistory("Agent", String(firstDefined([items.Text, items.text]) || ""));
        }
    } else if (serviceName === SERVICE_XIAOZHI && eventName === "ActivationCodeReceived") {
        activationCode = String(firstDefined([items.Code, items.code]) || "");
        setStatus("status.activation_code_received_with_code", activationCode);
        refreshUi();
        playXiaoZhiActivationCode(activationCode);
    } else if (serviceName === SERVICE_COZE && eventName === "CozeEventHappened") {
        handleCozeEventHappened(String(firstDefined([items.CozeEvent, items.coze_event, items.cozeEvent]) || ""));
    }
}

function wakeSleepingAgent() {
    if (!agentReady || !agentStarted || !agentSleeping || agentWakeSubmitted) return;
    agentWakeSubmitted = true;
    var epoch = navigationEpoch;
    callAsync(agentHandle, "TriggerGeneralAction", {Action: "WakeUp"}, 0).then(function (result) {
        if (!navigationAlive || epoch !== navigationEpoch) return;
        if (!result.success) {
            agentWakeSubmitted = false;
            setStatus("status.wakeup_failed", resultError(result));
            refreshUi();
        }
    });
}

async function openChatPage(action) {
    if (!await navigatePage("ai_chatbot_chat")) return;
    currentPage = PAGE_CHAT;
    configErrorLatched = false;
    hideErrorDialogIfVisible();
    resumeAgentIfSuspended();
    renderMissingHistory();
    if (agentSleeping) wakeSleepingAgent();
    else maybeStartAgent();
    refreshUi();
    scheduleLatestHistoryScroll(true);
}

async function openSettingsPage(action) {
    if (!await navigatePage("ai_chatbot_settings")) return;
    cancelLatestHistoryScroll();
    suspendAgentIfStarted();
    currentPage = PAGE_SETTINGS;
    refreshUi();
}

async function openAgentSelectPage(action) {
    if (!await navigatePage("ai_chatbot_select")) return;
    cancelLatestHistoryScroll();
    suspendAgentIfStarted();
    currentPage = PAGE_AGENT_SELECT;
    populateAgentOptions();
    refreshUi();
}

function startSupportServices() {
    coreHandle = startService("SystemCore");
    guiHandle = startService("SystemGui");
    timerHandle = startService("SystemTimer");
    if (coreHandle === 0 || guiHandle === 0) {
        log("Required SystemCore/SystemGui services are unavailable");
        return false;
    }
    return true;
}

function stopSupportServices() {
    disconnectAgentEvents();
    hideErrorDialogIfVisible();
    stopTimer(networkTimerId);
    stopTimer(initialRefreshTimerId);
    stopTimer(historyScrollTimerId);
    networkTimerId = 0;
    initialRefreshTimerId = 0;
    historyScrollTimerId = 0;
    releaseServices();
    stopService(timerHandle);
    stopService(guiHandle);
    stopService(coreHandle);
    timerHandle = 0;
    guiHandle = 0;
    coreHandle = 0;
}

function resetRuntimeState() {
    appliedBindings = {};
    currentPage = PAGE_CHAT;
    deviceReady = false;
    agentReady = false;
    networkReady = false;
    internetReady = false;
    agentStarted = false;
    agentSleeping = false;
    agentWakeSubmitted = false;
    agentStartSubmitted = false;
    agentSuspendedByApp = false;
    agentSuspended = false;
    agentSpeaking = false;
    agentListening = false;
    configErrorLatched = false;
    selectedAgentName = "";
    activationCode = "-";
    networkDetail = localized("network.checking");
    agentState = localized("state.unavailable");
    cloudState = localized("cloud.disconnected");
    statusText = localized("status.starting");
    agentAttributes = [];
    agentItems = [];
    history = [];
    nextHistoryItemId = 0;
}

// ESPocket owns the only page stack. Synchronize business state after Back as well.
var navigationEpoch = 0;
var navigationAlive = false;
var navigationBusy = false;
var navigationPolling = false;
var navigationRevision = 0;
var navigationTimerId = 0;
var NAVIGATION_TIMER_NAME = "espocket.chatbot.navigation";

async function navigationRequest(request) {
    return JSON.parse(await espocketNavigation.dispatch(JSON.stringify(request)));
}

function synchronizeNavigation(pageId) {
    var next = pageId === "ai_chatbot_chat" ? PAGE_CHAT :
        pageId === "ai_chatbot_settings" ? PAGE_SETTINGS : PAGE_AGENT_SELECT;
    if (next === currentPage) return;
    currentPage = next;
    if (next === PAGE_CHAT) {
        configErrorLatched = false;
        hideErrorDialogIfVisible();
        resumeAgentIfSuspended();
        renderMissingHistory();
        maybeStartAgent();
        scheduleLatestHistoryScroll(true);
    } else {
        cancelLatestHistoryScroll();
        suspendAgentIfStarted();
        if (next === PAGE_AGENT_SELECT) populateAgentOptions();
    }
    refreshUi();
}

async function navigatePage(target) {
    if (!navigationAlive || navigationBusy) return false;
    var epoch = navigationEpoch;
    navigationBusy = true;
    ++navigationRevision;
    try {
        var page = await navigationRequest({operation: "snapshot"});
        if (!navigationAlive || epoch !== navigationEpoch) return false;
        if (page.pageId !== target) {
            var request = target === "ai_chatbot_chat" ? {operation: "resetToRoot"} :
                target === "ai_chatbot_settings" && page.pageId === "ai_chatbot_select" ?
                    {operation: "requestBack"} : {operation: "push", pageId: target};
            page = await navigationRequest(request);
        }
        if (!navigationAlive || epoch !== navigationEpoch) return false;
        return page.pageId === target;
    } catch (error) {
        log("Navigation failed: " + String(error));
        return false;
    } finally {
        if (epoch === navigationEpoch) navigationBusy = false;
    }
}

async function pollNavigation() {
    if (!navigationAlive || navigationBusy || navigationPolling) return;
    var epoch = navigationEpoch;
    var revision = navigationRevision;
    navigationPolling = true;
    try {
        var page = await navigationRequest({operation: "snapshot"});
        if (navigationAlive && epoch === navigationEpoch && !navigationBusy &&
                revision === navigationRevision) synchronizeNavigation(page.pageId);
    } catch (error) {
        log("Navigation snapshot failed: " + String(error));
    } finally {
        if (epoch === navigationEpoch) navigationPolling = false;
    }
}

var brookesia_app = globalThis.brookesia_app = {};

brookesia_app.on_start = function () {
    log("starting");
    resetRuntimeState();
    if (!startSupportServices()) {
        stopSupportServices();
        return false;
    }
    ++navigationEpoch;
    navigationAlive = true;
    navigationBusy = false;
    navigationPolling = false;
    ++navigationRevision;
    navigationTimerId = startPeriodicTimer(NAVIGATION_TIMER_NAME, 100);
    applyLocale();
    subscribeActions();
    bindServices();
    loadAgentsAndTarget();
    subscribeAgentEvents();
    networkTimerId = startPeriodicTimer(NETWORK_TIMER_NAME, NETWORK_POLL_INTERVAL_MS);
    initialRefreshTimerId = startDelayedTimer(INITIAL_REFRESH_TIMER_NAME, INITIAL_REFRESH_DELAY_MS);
    if (initialRefreshTimerId === 0) {
        pollNetworkAndMaybeStart();
    }
    refreshUi();
    return true;
};

brookesia_app.on_action = function (action, path) {
    if (action === ACTION_CHAT_OPEN_CHAT || action === ACTION_SETTINGS_OPEN_CHAT) {
        openChatPage(action);
    } else if (action === ACTION_CHAT_OPEN_SETTINGS || action === ACTION_SETTINGS_OPEN_SETTINGS ||
               action === ACTION_SELECT_BACK || action === ACTION_SELECT_BACK_SETTINGS) {
        openSettingsPage(action);
    } else if (action === ACTION_SETTINGS_OPEN_AGENT_SELECT) {
        openAgentSelectPage(action);
    } else if (action === ACTION_CLEAR_HISTORY) {
        clearHistory();
        refreshUi();
    } else if (action === ACTION_SELECT_AGENT) {
        handleAgentSelectPath(path);
    }
    return true;
};

brookesia_app.on_event = function (serviceName, eventName, itemsJson) {
    handleServiceEvent(serviceName, eventName, itemsJson);
    return true;
};

brookesia_app.on_timer = function (timerId, name) {
    if (timerId === navigationTimerId && name === NAVIGATION_TIMER_NAME) {
        pollNavigation();
        return true;
    }
    if (timerId === initialRefreshTimerId && name === INITIAL_REFRESH_TIMER_NAME) {
        initialRefreshTimerId = 0;
        pollNetworkAndMaybeStart();
    } else if (timerId === networkTimerId && name === NETWORK_TIMER_NAME) {
        pollNetworkAndMaybeStart();
    } else if (timerId === historyScrollTimerId && name === HISTORY_SCROLL_TIMER_NAME) {
        historyScrollTimerId = 0;
        var animated = historyScrollAnimated;
        historyScrollAnimated = false;
        renderMissingHistory();
        refreshUi();
        scrollLatestHistoryIntoView(animated);
    }
    return true;
};

brookesia_app.on_stop = function () {
    ++navigationEpoch;
    navigationAlive = false;
    navigationBusy = false;
    navigationPolling = false;
    stopTimer(navigationTimerId);
    navigationTimerId = 0;
    log("stopping");
    stopAgent();
    clearHistory();
    clearAgentOptions();
    stopSupportServices();
    resetRuntimeState();
    return true;
};
