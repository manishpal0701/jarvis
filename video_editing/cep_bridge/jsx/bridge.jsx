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
            if (typeof app === "undefined" || !app || !app.project) {
                return JSON.stringify({
                    ok: true,
                    hasProject: false,
                    projectName: null,
                    sequenceName: null
                });
            }
            var p   = app.project;
            var seq = p.activeSequence;
            return JSON.stringify({
                ok:                true,
                hasProject:        true,
                projectName:       p.name,
                projectPath:       p.path,
                hasActiveSequence: seq ? true : false,
                sequenceName:      seq ? seq.name : null,
                sequenceId:        seq ? seq.sequenceID : null,
                videoTrackCount:   seq ? seq.videoTracks.numTracks : 0,
                audioTrackCount:   seq ? seq.audioTracks.numTracks : 0
            });
        } catch (e) {
            return _err(e);
        }
    }

    /**
     * Create a new Premiere project at the given path.
     * @param {string} name
     */
    function createProject(name) {
        try {
            var projectName = name || "Jarvis_AI_Edit";
            var tempPath    = Folder.temp.fsName + "\\" + projectName + ".prproj";
            app.newProject(tempPath);
            return _ok({ projectName: projectName, path: tempPath });
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

    /**
     * Import a list of file paths into the active project.
     * @param {string} jsonPaths – JSON array of absolute file paths
     */
    function importFiles(jsonPaths) {
        try {
            var paths    = JSON.parse(jsonPaths);
            var p        = _getProject();
            var imported = [];
            for (var i = 0; i < paths.length; i++) {
                var f = new File(paths[i]);
                if (!f.exists) {
                    return _err("File not found: " + paths[i]);
                }
                p.importFiles([paths[i]], true, p.getInsertionBin(), false);
                imported.push(paths[i]);
            }
            return JSON.stringify({ ok: true, imported: imported });
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

            // Find the clip in project bin by media path
            var target = null;
            for (var i = 0; i < p.rootItem.children.numItems; i++) {
                var item = p.rootItem.children[i];
                try {
                    var mp = item.getMediaPath();
                    if (mp && mp.replace(/\\/g, "/") === clipPath.replace(/\\/g, "/")) {
                        target = item;
                        break;
                    }
                } catch (_) {}
            }

            // Fallback to last imported item
            if (!target && p.rootItem.children.numItems > 0) {
                target = p.rootItem.children[p.rootItem.children.numItems - 1];
            }

            if (!target) {
                throw new Error("Clip not found in project bin: " + clipPath);
            }

            var vTrack = seq.videoTracks[0];
            vTrack.overwriteClip(target, timelinePos);
            return _ok({ clipName: target.name, timelinePos: timelinePos });
        } catch (e) {
            return _err(e);
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
            version: "2.0.0",
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

        // Test: timeline API (videoTracks accessible)
        try {
            var seq = app && app.project && app.project.activeSequence;
            report.apis.timelineAPI = seq ? (typeof seq.videoTracks !== "undefined") : false;
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
            // Fallback: we're inside JarvisBridge so it's definitely loaded
            report.apis.bridgeLoaded = true;
        }

        return JSON.stringify(report);
    }

    // ── Public API ────────────────────────────────────────────────────

    return {
        diagnostic:          diagnostic,
        runCode:             runCode,
        getProjectInfo:      getProjectInfo,
        createProject:       createProject,
        ensureSequence:      ensureSequence,
        movePlayhead:        movePlayhead,
        createVideoTrack:    createVideoTrack,
        createAudioTrack:    createAudioTrack,
        importFiles:         importFiles,
        readTimeline:        readTimeline,
        placeClipOnTimeline: placeClipOnTimeline,
        selfTest:            selfTest
    };

})();

} // end guard: typeof $.global.JarvisBridge === "undefined"

// ── Confirm loading ───────────────────────────────────────────────────────────
// This line executes when Premiere Pro loads bridge.jsx via ScriptPath.
// The result "JarvisBridge:ready" appears in Premiere's ExtendScript console.
"JarvisBridge:ready";
