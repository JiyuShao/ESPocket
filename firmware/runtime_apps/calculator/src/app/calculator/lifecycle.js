var guiHandle = 0;

var FORMULA_PATH = "/calculator/page/display/formula";
var RESULT_PATH = "/calculator/page/display/result";
var HISTORY_PATH = "/calculator/page/display/history";

var ACTION_PREFIX = "calculator.key.";
var LOG_PREFIX = "[Calculator] ";

var formula = "0";
var history = "";
var resultText = "";
var errorState = false;
var justEvaluated = false;

var ACTIONS = [
    "calculator.key.clear",
    "calculator.key.divide",
    "calculator.key.multiply",
    "calculator.key.backspace",
    "calculator.key.digit_7",
    "calculator.key.digit_8",
    "calculator.key.digit_9",
    "calculator.key.subtract",
    "calculator.key.digit_4",
    "calculator.key.digit_5",
    "calculator.key.digit_6",
    "calculator.key.add",
    "calculator.key.digit_1",
    "calculator.key.digit_2",
    "calculator.key.digit_3",
    "calculator.key.percent",
    "calculator.key.digit_0",
    "calculator.key.decimal",
    "calculator.key.equals"
];

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

function call(handle, name, params) {
    try {
        return parseResult(brookesia.call_function(handle, name, JSON.stringify(params || {})));
    } catch (error) {
        return {success: false, error: errorText(error)};
    }
}

function gui(name, params) {
    if (guiHandle === 0) {
        return {success: false, error: "SystemGui service is not running"};
    }
    return call(guiHandle, name, params);
}

function bindingUpdate(path, key, value) {
    return {
        Path: path,
        Key: key,
        Value: String(value)
    };
}

function applyBindings(updates) {
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
    return result;
}

function subscribe(action) {
    var result = gui("SubscribeAction", {Action: action});
    if (!result.success) {
        log("SubscribeAction failed: " + action + ": " + (result.error || result.error_message || "unknown"));
    }
}

function flushUi() {
    applyBindings([
        bindingUpdate(FORMULA_PATH, "labelProps.text", formula),
        bindingUpdate(RESULT_PATH, "labelProps.text", resultText),
        bindingUpdate(HISTORY_PATH, "labelProps.text", history)
    ]);
}

function isOperator(ch) {
    return ch === "+" || ch === "-" || ch === "x" || ch === "/";
}

function lastChar() {
    return formula.length === 0 ? "" : formula.charAt(formula.length - 1);
}

function resetForFreshInput() {
    if (errorState || justEvaluated) {
        formula = "0";
        resultText = "";
        errorState = false;
        justEvaluated = false;
    }
}

function activeNumberText() {
    var start = 0;
    for (var i = formula.length - 1; i >= 0; --i) {
        var ch = formula.charAt(i);
        if (isOperator(ch)) {
            if (i === 0 && ch === "-") {
                start = 0;
            } else {
                start = i + 1;
            }
            break;
        }
    }
    return formula.slice(start);
}

function appendDigit(digit) {
    resetForFreshInput();
    if (formula === "0") {
        formula = digit;
    } else if (formula === "-0") {
        formula = "-" + digit;
    } else {
        formula += digit;
    }
    preview();
}

function appendDecimal() {
    resetForFreshInput();
    var number = activeNumberText();
    if (number.indexOf(".") >= 0 || number.indexOf("%") >= 0) {
        return;
    }
    if (formula === "0" || isOperator(lastChar())) {
        formula += "0.";
    } else if (formula === "-") {
        formula += "0.";
    } else {
        formula += ".";
    }
    preview();
}

function appendOperator(op) {
    if (errorState) {
        clear();
    }
    justEvaluated = false;
    var last = lastChar();
    if (formula === "0" && op === "-") {
        formula = "-";
        resultText = "";
        flushUi();
        return;
    }
    if (last === "" || last === ".") {
        return;
    }
    if (isOperator(last)) {
        formula = formula.slice(0, -1) + op;
    } else {
        formula += op;
    }
    preview();
}

function appendPercent() {
    resetForFreshInput();
    var number = activeNumberText();
    var last = lastChar();
    if (number.length === 0 || number.indexOf("%") >= 0 || !(last >= "0" && last <= "9")) {
        return;
    }
    formula += "%";
    preview();
}

function backspace() {
    if (errorState || justEvaluated) {
        clear();
        return;
    }
    if (formula.length <= 1) {
        formula = "0";
    } else {
        formula = formula.slice(0, -1);
        if (formula === "-" || formula.length === 0) {
            formula = "0";
        }
    }
    preview();
}

function clear() {
    formula = "0";
    history = "";
    resultText = "";
    errorState = false;
    justEvaluated = false;
    flushUi();
}

function pushCurrentNumber(tokens, current) {
    if (current.length === 0 || current === "-") {
        return false;
    }
    var value = parseFloat(current);
    if (!isFinite(value)) {
        return false;
    }
    tokens.push(value);
    return true;
}

function tokenize(text) {
    var tokens = [];
    var current = "";
    var lastWasNumber = false;

    for (var i = 0; i < text.length; ++i) {
        var ch = text.charAt(i);
        if ((ch >= "0" && ch <= "9") || ch === ".") {
            current += ch;
            lastWasNumber = false;
        } else if (ch === "%") {
            if (!pushCurrentNumber(tokens, current)) {
                return null;
            }
            tokens[tokens.length - 1] = tokens[tokens.length - 1] / 100;
            current = "";
            lastWasNumber = true;
        } else if (isOperator(ch)) {
            if (current.length > 0) {
                if (!pushCurrentNumber(tokens, current)) {
                    return null;
                }
                current = "";
                lastWasNumber = true;
            }
            if (ch === "-" && !lastWasNumber && tokens.length === 0) {
                current = "-";
                continue;
            }
            if (!lastWasNumber) {
                return null;
            }
            tokens.push(ch);
            lastWasNumber = false;
        } else {
            return null;
        }
    }

    if (current.length > 0) {
        if (!pushCurrentNumber(tokens, current)) {
            return null;
        }
        lastWasNumber = true;
    }
    if (tokens.length === 0 || !lastWasNumber) {
        return null;
    }
    return tokens;
}

function reduceMulDiv(tokens) {
    var out = [];
    for (var i = 0; i < tokens.length; ++i) {
        var token = tokens[i];
        if (token === "x" || token === "/") {
            if (out.length === 0 || i + 1 >= tokens.length) {
                return null;
            }
            var lhs = out.pop();
            var rhs = tokens[++i];
            if (typeof lhs !== "number" || typeof rhs !== "number") {
                return null;
            }
            if (token === "/" && Math.abs(rhs) < 0.000000001) {
                return null;
            }
            out.push(token === "x" ? lhs * rhs : lhs / rhs);
        } else {
            out.push(token);
        }
    }
    return out;
}

function evaluate(text) {
    var tokens = tokenize(text);
    if (!tokens) {
        return null;
    }
    tokens = reduceMulDiv(tokens);
    if (!tokens) {
        return null;
    }
    var value = tokens[0];
    for (var i = 1; i < tokens.length; i += 2) {
        var op = tokens[i];
        var rhs = tokens[i + 1];
        if (typeof rhs !== "number") {
            return null;
        }
        if (op === "+") {
            value += rhs;
        } else if (op === "-") {
            value -= rhs;
        } else {
            return null;
        }
    }
    return value;
}

function formatNumber(value) {
    if (value === null || !isFinite(value)) {
        return "";
    }
    if (Math.abs(value - Math.round(value)) < 0.0000001) {
        return String(Math.round(value));
    }
    var text = value.toFixed(8);
    while (text.indexOf(".") >= 0 && text.charAt(text.length - 1) === "0") {
        text = text.slice(0, -1);
    }
    if (text.charAt(text.length - 1) === ".") {
        text = text.slice(0, -1);
    }
    return text;
}

function canPreview() {
    var last = lastChar();
    return formula !== "-" && last !== "." && !isOperator(last);
}

function preview() {
    var value = canPreview() ? evaluate(formula) : null;
    resultText = value === null ? "" : formatNumber(value);
    flushUi();
}

function equals() {
    var value = canPreview() ? evaluate(formula) : null;
    if (value === null) {
        resultText = "Error";
        errorState = true;
        justEvaluated = false;
        flushUi();
        return;
    }
    var output = formatNumber(value);
    history = formula + " =";
    formula = output;
    resultText = "";
    errorState = false;
    justEvaluated = true;
    flushUi();
}

function handleKey(key) {
    if (key.indexOf("digit_") === 0) {
        appendDigit(key.slice("digit_".length));
    } else if (key === "decimal") {
        appendDecimal();
    } else if (key === "add") {
        appendOperator("+");
    } else if (key === "subtract") {
        appendOperator("-");
    } else if (key === "multiply") {
        appendOperator("x");
    } else if (key === "divide") {
        appendOperator("/");
    } else if (key === "percent") {
        appendPercent();
    } else if (key === "backspace") {
        backspace();
    } else if (key === "clear") {
        clear();
    } else if (key === "equals") {
        equals();
    }
}

var brookesia_app = globalThis.brookesia_app = {};

brookesia_app.on_start = function () {
    guiHandle = brookesia.start_service("SystemGui") || 0;
    if (guiHandle === 0) {
        log("Failed to start SystemGui service");
        return false;
    }
    for (var i = 0; i < ACTIONS.length; ++i) {
        subscribe(ACTIONS[i]);
    }
    flushUi();
    return true;
};

brookesia_app.on_action = function (action) {
    if (action.indexOf(ACTION_PREFIX) !== 0) {
        return true;
    }
    handleKey(action.slice(ACTION_PREFIX.length));
    return true;
};

brookesia_app.on_stop = function () {
    if (guiHandle !== 0) {
        try {
            brookesia.stop_service(guiHandle);
        } catch (error) {
            log("Failed to stop SystemGui: " + errorText(error));
        }
        guiHandle = 0;
    }
    return true;
};
