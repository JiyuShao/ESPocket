// App-local result ownership. Invalidating a ticket never cancels a submitted
// Brookesia operation or changes the Agent's real lifecycle state.
export function createChatOperations(readOwner) {
    var pending = Object.create(null);
    var agentRevision = 0;
    var dependencies = {
        discovery: ["agent"],
        network: ["device"],
        configure: ["agent", "storage", "target"],
        start: ["agent", "target"],
        wake: ["agent", "target"]
    };
    function agentScoped(kind) {
        return kind === "configure" || kind === "start" || kind === "wake";
    }
    function current(ticket) {
        if (!ticket || pending[ticket.kind] !== ticket) return false;
        var owner = readOwner();
        if (!owner.alive || owner.instance !== ticket.owner.instance) return false;
        if (agentScoped(ticket.kind) && agentRevision !== ticket.agentRevision) return false;
        return dependencies[ticket.kind].every(function (key) {
            return owner[key] === ticket.owner[key];
        });
    }
    return {
        begin: function (kind) {
            if (!dependencies[kind]) throw new Error("Unknown Chat operation: " + kind);
            var ticket = {kind: kind, owner: readOwner(), agentRevision: agentRevision};
            pending[kind] = ticket;
            return ticket;
        },
        current: current,
        pending: function (kind) { return current(pending[kind]); },
        finish: function (ticket) {
            if (!current(ticket)) return false;
            delete pending[ticket.kind];
            return true;
        },
        clear: function (kind) { delete pending[kind]; },
        invalidateAgent: function () {
            ++agentRevision;
            Object.keys(pending).forEach(function (kind) {
                if (agentScoped(kind)) delete pending[kind];
            });
        },
        reset: function () { pending = Object.create(null); ++agentRevision; }
    };
}
