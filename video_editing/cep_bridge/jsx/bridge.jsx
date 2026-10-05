/**
 * Jarvis Bridge – ExtendScript (bridge.jsx)
 * ==========================================
 * Runs inside Adobe Premiere Pro's ExtendScript engine.
 * Loaded automatically by Premiere Pro via the ScriptPath in manifest.xml.
 * Called by the CEP panel (index.html) via cs.evalScript() / CSInterface.evalScript().
 *
 * IMPORTANT:
 *   - This file executes in Premiere Pro's JSENGINE (ExtendScript), NOT in the browser/Node.js.
 *   - The 'app' object is the Premiere Pro application object — always available in ExtendScript.
 *   - All public functions return a JSON STRING: { ok, result, error }
 *     so the Python layer can always do response.json().
 *   - JarvisBridge is assigned to the global scope ($.global) so it persists across evalScript() calls.
 */

// ── Guard against double-loading ──────────────────────────────────────────────
// If this file is evaluated multiple times, skip re-definition.
if (typeof $.global.JarvisBridge === "undefined") {

$.global.JarvisBridge = (function () {

    // ── Internal helpers ──────────────────────────────────────────────

    function _ok(result) {
        return JSON.stringify({ ok: true, result: result });
    }

    function _err(msg) {
        return JSON.stringify({ ok: false, error: String(msg) });
    }

    function _getProject() {
        if (typeof app === "undefined" || app === null) {
            throw new Error("app object not accessible. Premiere Pro may still be loading.");
        }
        if (!app.project) {
            throw new Error("No active project. Please open or create a project in Premiere Pro.");
        }
        return app.project;
    }

    function _getSequence() {
        var p = _getProject();
        if (!p.activeSequence) {
            throw new Error("No active sequence. Please create a sequence first.");
        }
        return p.activeSequence;
    }

    // ── Diagnostic: verify environment from inside ExtendScript ──────

    /**
     * Minimal environment diagnostic. Called first by Python to verify
     * that the ExtendScript context is working correctly.
     * Returns: { ok, typeofApp, appName, version, hasProject, bridgeLoaded }
     */
    function diagnostic() {
        var result = {
            ok:           true,
            typeofApp:    typeof app,
            appLoaded:    false,
            appName:      "unknown",
            version:      "unknown",
            hasProject:   false,
            bridgeLoaded: true  // if we're here, bridge loaded
        };

        try {
            if (typeof app !== "undefined" && app !== null) {
                result.appLoaded = true;
                result.appName   = app.name || "unknown";
                result.version   = app.version || "unknown";
                result.hasProject = !!(app.project);
            }
        } catch (e) {
            result.appError = String(e);
        }

        return JSON.stringify(result);
    }

    // ── Core execution ────────────────────────────────────────────────

    /**
     * Execute arbitrary ExtendScript sent from Python.
     * @param {string} code
     */
    function runCode(code) {
        try {
            var result = eval(code); // eslint-disable-line no-eval
            if (typeof result === "string") {
                // If result is already a JSON string, pass through directly
                try {
                    JSON.parse(result);
                    return result;
                } catch (_) {}
            }
            return _ok(result !== undefined ? String(result) : "undefined");
        } catch (e) {
            return _err(e);
        }
    }

    // ── Project API ───────────────────────────────────────────────────

    /**
     * Return comprehensive project + sequence info.
     */
    function getProjectInfo() {
        try {
            if (typeof app === "undefined" || !app) {
                return JSON.stringify({
                    ok: true,
                    appLoaded: false,
                    hasProject: false,
                    rootItemAccessible: false,
                    projectName: null,
                    sequenceName: null
                });
            }
            if (typeof app.enableQE === "function") {
                try { app.enableQE(); } catch (_) {}
            }
            var p = app.project;
            if (!p) {
                return JSON.stringify({
                    ok: true,
                    appLoaded: true,
                    hasProject: false,
                    rootItemAccessible: false,
                    projectName: null,
                    sequenceName: null
                });
            }
            var seq = p.activeSequence;
            var rootItemOk = false;
            try { rootItemOk = !!(p.rootItem); } catch (_) {}
            return JSON.stringify({
                ok:                true,
                appLoaded:         true,
                hasProject:        true,
                rootItemAccessible:rootItemOk,
                projectName:       p.name,
                projectPath:       p.path,
                hasActiveSequence: seq ? true : false,
                sequenceName:      seq ? seq.name : null,
                sequenceId:        seq ? seq.sequenceID : null,
                videoTrackCount:   seq ? seq.videoTracks ? seq.videoTracks.numTracks : 0 : 0,
                audioTrackCount:   seq ? seq.audioTracks ? seq.audioTracks.numTracks : 0 : 0
            });
        } catch (e) {
            return _err(e);
        }
    }

    /**
     * Create a new Premiere project at the given path or name.
     * @param {string} name
     * @param {string} targetPath
     */
    function createProject(name, targetPath) {
        try {
            var projectName = name || "Jarvis_AI_Edit";
            if (typeof app !== "undefined" && app && app.project && app.project.name) {
                return _ok({ projectName: app.project.name, path: app.project.path, alreadyOpen: true });
            }
            var savePath = targetPath || "";
            savePath = savePath.replace(/\\/g, "/");

            if (app && app.project) {
                try { app.project.closeDocument(false, true); } catch (_) {}
            }

            if (typeof app !== "undefined" && app) {
                if (savePath && savePath.length > 0) {
                    var fObj = new File(savePath);
                    if (fObj.exists && typeof app.openDocument === "function") {
                        try {
                            app.openDocument(savePath);
                        } catch (_) {}
                    }
                }
                if ((!app.project || !app.project.name) && typeof app.newProject === "function") {
                    try {
                        var newProjArg = (savePath && savePath.length > 0) ? savePath : projectName;
                        app.newProject(newProjArg);
                    } catch (e1) {
                        try { app.newProject(); } catch (e2) {}
                    }
                }
            }

            if (app && app.project && savePath) {
                try {
                    app.project.saveAs(savePath);
                } catch (_) {}
            }

            if (app && app.project) {
                return _ok({ projectName: app.project.name || projectName, path: savePath, created: true });
            }
            throw new Error("ExtendScript app.newProject failed to initialize project at path: " + savePath);
        } catch (e) {
            return _err(e);
        }
    }

    // ── Sequence API ──────────────────────────────────────────────────

    /**
     * Ensure an active sequence exists, creating one if needed.
     * @param {string} name
     */
    function ensureSequence(name) {
        try {
            var p      = _getProject();
            var seq    = p.activeSequence;
            if (!seq) {
                var seqName = name || "Jarvis_Master_Edit";
                p.createNewSequence(seqName, seqName.replace(/ /g, "_").toUpperCase());
                seq = p.activeSequence;
            }
            if (!seq) {
                throw new Error("Sequence creation failed — p.createNewSequence did not set p.activeSequence.");
            }
            return JSON.stringify({ ok: true, name: seq.name, id: seq.sequenceID });
        } catch (e) {
            return _err(e);
        }
    }

    /**
     * Move the playhead to a given position (in seconds).
     * @param {number} seconds
     */
    function movePlayhead(seconds) {
        try {
            var seq   = _getSequence();
            var ticks = seconds * 254016000000; // Premiere ticks per second
            seq.setPlayerPosition(String(Math.round(ticks)));
            return _ok({ positionSeconds: seconds });
        } catch (e) {
            return _err(e);
        }
    }

    // ── Track API ─────────────────────────────────────────────────────

    function createVideoTrack() {
        try {
            var seq = _getSequence();
            seq.videoTracks.add();
            return _ok({ videoTrackCount: seq.videoTracks.numTracks });
        } catch (e) {
            return _err(e);
        }
    }

    function createAudioTrack() {
        try {
            var seq = _getSequence();
            seq.audioTracks.add();
            return _ok({ audioTrackCount: seq.audioTracks.numTracks });
        } catch (e) {
            return _err(e);
        }
    }

    // ── Import API ────────────────────────────────────────────────────

    function _normalizePath(p) {
        if (!p) return "";
        return String(p).replace(/\//g, "\\").toLowerCase().replace(/\\+/g, "\\");
    }

    function _collectProjectItems(item, itemsList) {
        if (!item) return;
        try {
            var mp = item.getMediaPath ? item.getMediaPath() : null;
            if (mp) {
                itemsList.push({
                    name: item.name || "",
                    mediaPath: mp,
                    type: item.type || 0
                });
            }
        } catch (_) {}
        if (item.children && item.children.numItems > 0) {
            for (var i = 0; i < item.children.numItems; i++) {
                _collectProjectItems(item.children[i], itemsList);
            }
        }
    }

    function getProjectItems() {
        try {
            var p = _getProject();
            var items = [];
            _collectProjectItems(p.rootItem, items);
            return JSON.stringify({ ok: true, count: items.length, items: items });
        } catch (e) {
            return _err(e);
        }
    }

    /**
     * Import a list of file paths into the active project.
     * @param {string} jsonPaths – JSON array of absolute file paths
     */
    function importFiles(jsonPaths) {
        try {
            var paths    = JSON.parse(jsonPaths);
            var p        = _getProject();
            var imported = [];
            var targetBin = null;
            try {
                if (typeof p.getInsertionBin === "function") {
                    targetBin = p.getInsertionBin();
                }
            } catch (_) {}
            if (!targetBin) { targetBin = p.rootItem; }

            for (var i = 0; i < paths.length; i++) {
                var f = new File(paths[i]);
                if (!f.exists) {
                    return _err("File not found: " + paths[i]);
                }
                var importPath = f.fsName || paths[i];
                p.importFiles([importPath], true, targetBin, false);
                imported.push(paths[i]);
            }
            return JSON.stringify({ ok: true, imported: imported });
        } catch (e) {
            return _err(e);
        }
    }

    function saveProject() {
        try {
            var p = _getProject();
            p.save();
            return _ok({ saved: true, path: p.path, name: p.name });
        } catch (e) {
            return _err(e);
        }
    }

    // ── Timeline API ──────────────────────────────────────────────────

    /**
     * Read the active timeline: all clips on all video tracks.
     */
    function readTimeline() {
        try {
            var seq   = _getSequence();
            var clips = [];
            for (var t = 0; t < seq.videoTracks.numTracks; t++) {
                var track = seq.videoTracks[t];
                for (var c = 0; c < track.clips.numItems; c++) {
                    var clip = track.clips[c];
                    try {
                        clips.push({
                            track:    t,
                            index:    c,
                            name:     clip.name,
                            start:    clip.start.seconds,
                            end:      clip.end.seconds,
                            duration: clip.duration.seconds,
                            inPoint:  clip.inPoint.seconds,
                            outPoint: clip.outPoint.seconds
                        });
                    } catch (_) {}
                }
            }
            return JSON.stringify({ ok: true, clipCount: clips.length, clips: clips });
        } catch (e) {
            return _err(e);
        }
    }

    /**
     * Place a clip on V1 at a given timeline position (seconds).
     * @param {string} clipPath
     * @param {number} timelinePos
     */
    function placeClipOnTimeline(clipPath, timelinePos) {
        try {
            var p   = _getProject();
            var seq = _getSequence();
            var target = _findProjectItemByPath(clipPath);
            var vTrack = seq.videoTracks[0];
            vTrack.overwriteClip(target, timelinePos);
            return _ok({ clipName: target.name, timelinePos: timelinePos });
        } catch (e) {
            return _err(e);
        }
    }

    // ── Canonical Time Conversion Layer ──────────────────────────────
    var TICKS_PER_SECOND = 254016000000;

    function _secondsToTicks(sec) {
        return Math.round(Number(sec) * TICKS_PER_SECOND);
    }

    function _ticksToSeconds(ticks) {
        return Number(ticks) / TICKS_PER_SECOND;
    }

    function _setTimeProperty(timeObj, seconds) {
        if (!timeObj) return;
        try {
            if (typeof timeObj.seconds !== "undefined") {
                timeObj.seconds = Number(seconds);
            } else if (typeof timeObj.ticks !== "undefined") {
                timeObj.ticks = String(_secondsToTicks(seconds));
            }
        } catch (_) {}
    }

    // ── Track & Clip Resolution Helpers ──────────────────────────────

    function _getVideoTrack(trackIndex) {
        var seq = _getSequence();
        var idx = Number(trackIndex || 0);
        while (seq.videoTracks.numTracks <= idx) {
            seq.videoTracks.add();
        }
        return seq.videoTracks[idx];
    }

    function _getAudioTrack(trackIndex) {
        var seq = _getSequence();
        var idx = Number(trackIndex || 0);
        while (seq.audioTracks.numTracks <= idx) {
            seq.audioTracks.add();
        }
        return seq.audioTracks[idx];
    }

    function _getTrack(trackType, trackIndex) {
        if (String(trackType).toLowerCase() === "audio") {
            return _getAudioTrack(trackIndex);
        }
        return _getVideoTrack(trackIndex);
    }

    function _getClipOnTrack(trackObj, clipIndex) {
        var idx = Number(clipIndex);
        if (!trackObj || !trackObj.clips || idx < 0 || idx >= trackObj.clips.numItems) {
            throw new Error("Clip index " + idx + " out of bounds. Track has " + (trackObj ? trackObj.clips.numItems : 0) + " clips.");
        }
        return trackObj.clips[idx];
    }

    function _searchItemTree(item, normTarget) {
        if (!item) return null;
        try {
            var mp = item.getMediaPath ? item.getMediaPath() : null;
            if (mp && _normalizePath(mp) === normTarget) {
                return item;
            }
        } catch (_) {}
        if (item.children && item.children.numItems > 0) {
            for (var i = 0; i < item.children.numItems; i++) {
                var found = _searchItemTree(item.children[i], normTarget);
                if (found) return found;
            }
        }
        return null;
    }

    function _findProjectItemByPath(clipPath) {
        var p = _getProject();
        var normTarget = _normalizePath(clipPath);
        var found = _searchItemTree(p.rootItem, normTarget);
        if (found) return found;
        throw new Error("Clip not found in project bin: " + clipPath);
    }

    // ── Granular Timeline Functions ──────────────────────────────────

    function insertClipOnTimeline(clipPath, timelinePos, trackType, trackIndex) {
        try {
            var target = _findProjectItemByPath(clipPath);
            var track = _getTrack(trackType, trackIndex);
            var pos = Number(timelinePos || 0);
            if (typeof track.insertClip === "function") {
                track.insertClip(target, pos);
            } else {
                track.overwriteClip(target, pos);
            }
            return _ok({
                action: "insertClip",
                clipName: target.name,
                trackType: trackType || "video",
                trackIndex: Number(trackIndex || 0),
                timelinePos: pos
            });
        } catch (e) {
            return _err(e);
        }
    }

    function moveClipOnTimeline(trackType, trackIndex, clipIndex, newPos) {
        try {
            var track = _getTrack(trackType, trackIndex);
            var clip = _getClipOnTrack(track, clipIndex);
            var pos = Number(newPos || 0);
            _setTimeProperty(clip.start, pos);
            return _ok({
                action: "moveClip",
                clipName: clip.name,
                trackType: trackType,
                trackIndex: Number(trackIndex),
                clipIndex: Number(clipIndex),
                newStart: pos
            });
        } catch (e) {
            return _err(e);
        }
    }

    function trimClipOnTimeline(trackType, trackIndex, clipIndex, inTime, outTime) {
        try {
            var track = _getTrack(trackType, trackIndex);
            var clip = _getClipOnTrack(track, clipIndex);
            if (inTime !== null && inTime !== undefined) {
                _setTimeProperty(clip.inPoint, inTime);
            }
            if (outTime !== null && outTime !== undefined) {
                _setTimeProperty(clip.outPoint, outTime);
            }
            return _ok({
                action: "trimClip",
                clipName: clip.name,
                trackType: trackType,
                trackIndex: Number(trackIndex),
                clipIndex: Number(clipIndex),
                inPoint: clip.inPoint ? clip.inPoint.seconds : null,
                outPoint: clip.outPoint ? clip.outPoint.seconds : null
            });
        } catch (e) {
            return _err(e);
        }
    }

    function splitClipOnTimeline(trackType, trackIndex, clipIndex, splitTime) {
        try {
            var track = _getTrack(trackType, trackIndex);
            var clip = _getClipOnTrack(track, clipIndex);
            var st = Number(splitTime);

            var clipStart = clip.start ? clip.start.seconds : 0;
            var clipEnd = clip.end ? clip.end.seconds : 0;

            if (st <= clipStart || st >= clipEnd) {
                throw new Error("Split time (" + st + "s) must be between clip start (" + clipStart + "s) and end (" + clipEnd + "s).");
            }

            var origInPoint = clip.inPoint ? clip.inPoint.seconds : 0;
            var offsetInClip = st - clipStart;
            var splitInPoint = origInPoint + offsetInClip;

            _setTimeProperty(clip.outPoint, splitInPoint);

            var mediaPath = null;
            try { mediaPath = clip.projectItem ? clip.projectItem.getMediaPath() : null; } catch (_) {}

            if (mediaPath) {
                var item = _findProjectItemByPath(mediaPath);
                track.overwriteClip(item, st);
                var newClip = track.clips[track.clips.numItems - 1];
                _setTimeProperty(newClip.inPoint, splitInPoint);
            }

            return _ok({
                action: "splitClip",
                clipName: clip.name,
                trackType: trackType,
                trackIndex: Number(trackIndex),
                clipIndex: Number(clipIndex),
                splitTime: st
            });
        } catch (e) {
            return _err(e);
        }
    }

    function deleteClipOnTimeline(trackType, trackIndex, clipIndex, ripple) {
        try {
            var track = _getTrack(trackType, trackIndex);
            var clip = _getClipOnTrack(track, clipIndex);
            var clipName = clip.name;
            var isRipple = !!ripple;
            if (typeof clip.remove === "function") {
                clip.remove(isRipple, isRipple);
            } else {
                throw new Error("clip.remove method not supported on this ExtendScript environment.");
            }
            return _ok({
                action: "deleteClip",
                clipName: clipName,
                trackType: trackType,
                trackIndex: Number(trackIndex),
                clipIndex: Number(clipIndex),
                ripple: isRipple
            });
        } catch (e) {
            return _err(e);
        }
    }

    function readTimelineDetailed() {
        try {
            var seq = _getSequence();
            var videoClips = [];
            var audioClips = [];

            for (var v = 0; v < seq.videoTracks.numTracks; v++) {
                var vt = seq.videoTracks[v];
                for (var vc = 0; vc < vt.clips.numItems; vc++) {
                    var c = vt.clips[vc];
                    try {
                        var mp = c.projectItem ? c.projectItem.getMediaPath() : null;
                        videoClips.push({
                            trackType: "video",
                            trackIndex: v,
                            clipIndex: vc,
                            name: c.name,
                            start: c.start ? c.start.seconds : 0,
                            end: c.end ? c.end.seconds : 0,
                            duration: c.duration ? c.duration.seconds : 0,
                            inPoint: c.inPoint ? c.inPoint.seconds : 0,
                            outPoint: c.outPoint ? c.outPoint.seconds : 0,
                            mediaPath: mp
                        });
                    } catch (_) {}
                }
            }

            for (var a = 0; a < seq.audioTracks.numTracks; a++) {
                var at = seq.audioTracks[a];
                for (var ac = 0; ac < at.clips.numItems; ac++) {
                    var acClip = at.clips[ac];
                    try {
                        var amp = acClip.projectItem ? acClip.projectItem.getMediaPath() : null;
                        audioClips.push({
                            trackType: "audio",
                            trackIndex: a,
                            clipIndex: ac,
                            name: acClip.name,
                            start: acClip.start ? acClip.start.seconds : 0,
                            end: acClip.end ? acClip.end.seconds : 0,
                            duration: acClip.duration ? acClip.duration.seconds : 0,
                            inPoint: acClip.inPoint ? acClip.inPoint.seconds : 0,
                            outPoint: acClip.outPoint ? acClip.outPoint.seconds : 0,
                            mediaPath: amp
                        });
                    } catch (_) {}
                }
            }

            return JSON.stringify({
                ok: true,
                videoTrackCount: seq.videoTracks.numTracks,
                audioTrackCount: seq.audioTracks.numTracks,
                videoClipCount: videoClips.length,
                audioClipCount: audioClips.length,
                videoClips: videoClips,
                audioClips: audioClips,
                clips: videoClips.concat(audioClips)
            });
        } catch (e) {
            return _err(e);
        }
    }

    function applyTransitionOnTimeline(trackType, trackIndex, clipIndex, transitionType, duration) {
        try {
            var track = _getTrack(trackType, trackIndex);
            var clip = _getClipOnTrack(track, clipIndex);
            var tt = String(transitionType || "cut").toLowerCase();

            if (tt === "cut") {
                return _ok({ action: "applyTransition", transitionType: "cut", clipName: clip.name });
            }

            if (typeof clip.addTransition === "function") {
                clip.addTransition(tt, Number(duration || 1.0));
                return _ok({ action: "applyTransition", transitionType: tt, duration: Number(duration || 1.0), clipName: clip.name });
            }

            return _err("NOT_SUPPORTED: Transition '" + tt + "' is not supported by current Premiere ExtendScript DOM version.");
        } catch (e) {
            return _err(e);
        }
    }

    function setVisualEffectOnTimeline(trackType, trackIndex, clipIndex, effectName, value) {
        try {
            var track = _getTrack(trackType, trackIndex);
            var clip = _getClipOnTrack(track, clipIndex);
            var eff = String(effectName || "").toLowerCase();

            if (clip.components && clip.components.numItems > 0) {
                for (var i = 0; i < clip.components.numItems; i++) {
                    var comp = clip.components[i];
                    if (comp.displayName && comp.displayName.toLowerCase().indexOf(eff) !== -1) {
                        if (comp.properties && comp.properties.numItems > 0) {
                            comp.properties[0].setValue(Number(value), true);
                            return _ok({ action: "setVisualEffect", effectName: eff, value: Number(value), clipName: clip.name });
                        }
                    }
                }
            }

            return _err("NOT_SUPPORTED: Visual effect '" + eff + "' is not supported by current Premiere ExtendScript DOM version.");
        } catch (e) {
            return _err(e);
        }
    }

    function exportSequenceOnTimeline(outputPath, presetPath, workAreaType) {
        try {
            var seq = _getSequence();
            var outP = String(outputPath || "").replace(/\\/g, "/");
            var workType = Number(workAreaType || 0);

            if (typeof seq.exportAsMediaDirect === "function") {
                var pPath = presetPath ? String(presetPath) : "";
                var res = seq.exportAsMediaDirect(outP, pPath, workType);
                return _ok({
                    action: "exportSequence",
                    status: "COMPLETED",
                    outputPath: outP,
                    sequenceName: seq.name
                });
            }

            return _err("NOT_SUPPORTED: Media export (exportAsMediaDirect) is not supported by current Premiere ExtendScript DOM version.");
        } catch (e) {
            return _err("EXPORT_FAILED: " + String(e));
        }
    }

    // ── Self-Test / Health Check ──────────────────────────────────────

    /**
     * Run all API checks and return a detailed capability report.
     * Called by the panel's /healthcheck endpoint.
     */
    function selfTest() {
        var report = {
            ok:      true,
            version: "3.0.0",
            apis:    {}
        };

        // Test: app object accessible
        try {
            report.apis.appObject = (typeof app !== "undefined" && app !== null);
            if (report.apis.appObject) {
                report.apis.appName    = app.name || "unknown";
                report.apis.appVersion = app.version || "unknown";
            }
        } catch (_) {
            report.apis.appObject = false;
        }

        // Test: project accessible
        try {
            report.apis.projectAPI = !!(app && app.project);
            if (app && app.project) {
                report.apis.projectName = app.project.name;
            }
        } catch (_) {
            report.apis.projectAPI = false;
        }

        // Test: sequence accessible
        try {
            report.apis.sequenceAPI = !!(app && app.project && app.project.activeSequence);
        } catch (_) {
            report.apis.sequenceAPI = false;
        }

        // Test: timeline API (createNewSequence or videoTracks accessible)
        try {
            report.apis.timelineAPI = !!(app && app.project && (app.project.activeSequence || typeof app.project.createNewSequence === "function"));
        } catch (_) {
            report.apis.timelineAPI = false;
        }

        // Test: import API
        try {
            report.apis.importAPI = !!(app && app.project && typeof app.project.importFiles === "function");
        } catch (_) {
            report.apis.importAPI = false;
        }

        // Test: JarvisBridge itself loaded (check via $.global)
        try {
            report.apis.bridgeLoaded = (typeof $.global.JarvisBridge === "object");
        } catch (_) {
            report.apis.bridgeLoaded = true;
        }

        return JSON.stringify(report);
    }

    // ── Public API ────────────────────────────────────────────────────

    return {
        diagnostic:               diagnostic,
        runCode:                  runCode,
        getProjectInfo:           getProjectInfo,
        getProjectItems:          getProjectItems,
        createProject:            createProject,
        ensureSequence:           ensureSequence,
        movePlayhead:             movePlayhead,
        createVideoTrack:         createVideoTrack,
        createAudioTrack:         createAudioTrack,
        importFiles:              importFiles,
        readTimeline:             readTimeline,
        readTimelineDetailed:     readTimelineDetailed,
        placeClipOnTimeline:      placeClipOnTimeline,
        insertClipOnTimeline:     insertClipOnTimeline,
        overwriteClipOnTimeline:  overwriteClipOnTimeline,
        moveClipOnTimeline:       moveClipOnTimeline,
        trimClipOnTimeline:       trimClipOnTimeline,
        splitClipOnTimeline:      splitClipOnTimeline,
        deleteClipOnTimeline:     deleteClipOnTimeline,
        applyTransitionOnTimeline:applyTransitionOnTimeline,
        setVisualEffectOnTimeline:setVisualEffectOnTimeline,
        exportSequenceOnTimeline: exportSequenceOnTimeline,
        selfTest:                 selfTest
    };

})();

} // end guard: typeof $.global.JarvisBridge === "undefined"

// ── Confirm loading ───────────────────────────────────────────────────────────
// This line executes when Premiere Pro loads bridge.jsx via ScriptPath.
// The result "JarvisBridge:ready" appears in Premiere's ExtendScript console.
"JarvisBridge:ready";
