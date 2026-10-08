export function createI18nBundle(callGui, constantPath) {
    var values = {};

    function envelopeValue(result, fallback) {
        if (!result || !result.success || !result.data) {
            return fallback;
        }
        if (Object.prototype.hasOwnProperty.call(result.data, "Value")) {
            return result.data.Value;
        }
        return fallback;
    }

    function load() {
        var result = callGui("GetConstant", {Path: constantPath});
        var nextValues = envelopeValue(result, {});
        values = nextValues && typeof nextValues === "object" ? nextValues : {};
        return values;
    }

    function text(key, fallback) {
        if (Object.prototype.hasOwnProperty.call(values, key)) {
            return String(values[key]);
        }
        return fallback !== undefined ? String(fallback) : key;
    }

    return {
        load: load,
        raw: function () {
            return values;
        },
        text: text
    };
}
