
        app.enableQE();
        var project = app.project;
        if (!project) {
            app.newProject("Jarvis AI Edit.prproj");
            project = app.project;
        }
        
        var sequence = project.activeSequence;
        if (!sequence) {
            project.createNewSequence("Master Edit", "MASTER");
            sequence = project.activeSequence;
        }

        // REAL-TIME EDITING STEPS
        
            try {
                var path0 = "C:/Users/manis/Videos/car\\WhatsApp Video 2026-07-04 at 10.51.24 PM.mp4";
                project.importFiles([path0], true, project.getInsertionBin(), false);
                var sequence = project.activeSequence;
                var videoTrack = sequence.videoTracks[0];
                
                // Find the imported project item by media path
                var importedItem0 = null;
                for (var j = 0; j < project.rootItem.children.numItems; j++) {
                    var item = project.rootItem.children[j];
                    if (item.getMediaPath && item.getMediaPath().replace(/\\/g, "\\") === path0) {
                        importedItem0 = item;
                        break;
                    }
                }
                
                if (importedItem0) {
                    videoTrack.overwriteClip(importedItem0, 0);
                } else {
                    // Fallback to index if path matching fails
                    videoTrack.overwriteClip(project.rootItem.children[project.rootItem.children.numItems - 1], 0);
                }
            } catch (err) {
                // Ignore and continue next clip
            }
            
            try {
                var path1 = "C:/Users/manis/Videos/car\\WhatsApp Video 2026-07-04 at 10.51.34 PM.mp4";
                project.importFiles([path1], true, project.getInsertionBin(), false);
                var sequence = project.activeSequence;
                var videoTrack = sequence.videoTracks[0];
                
                // Find the imported project item by media path
                var importedItem1 = null;
                for (var j = 0; j < project.rootItem.children.numItems; j++) {
                    var item = project.rootItem.children[j];
                    if (item.getMediaPath && item.getMediaPath().replace(/\\/g, "\\") === path1) {
                        importedItem1 = item;
                        break;
                    }
                }
                
                if (importedItem1) {
                    videoTrack.overwriteClip(importedItem1, 2.0);
                } else {
                    // Fallback to index if path matching fails
                    videoTrack.overwriteClip(project.rootItem.children[project.rootItem.children.numItems - 1], 2.0);
                }
            } catch (err) {
                // Ignore and continue next clip
            }
            
            try {
                var path2 = "C:/Users/manis/Videos/car\\WhatsApp Video 2026-07-04 at 10.51.41 PM.mp4";
                project.importFiles([path2], true, project.getInsertionBin(), false);
                var sequence = project.activeSequence;
                var videoTrack = sequence.videoTracks[0];
                
                // Find the imported project item by media path
                var importedItem2 = null;
                for (var j = 0; j < project.rootItem.children.numItems; j++) {
                    var item = project.rootItem.children[j];
                    if (item.getMediaPath && item.getMediaPath().replace(/\\/g, "\\") === path2) {
                        importedItem2 = item;
                        break;
                    }
                }
                
                if (importedItem2) {
                    videoTrack.overwriteClip(importedItem2, 4.0);
                } else {
                    // Fallback to index if path matching fails
                    videoTrack.overwriteClip(project.rootItem.children[project.rootItem.children.numItems - 1], 4.0);
                }
            } catch (err) {
                // Ignore and continue next clip
            }
            
            try {
                var path3 = "C:/Users/manis/Videos/car\\WhatsApp Video 2026-07-04 at 10.51.45 PM.mp4";
                project.importFiles([path3], true, project.getInsertionBin(), false);
                var sequence = project.activeSequence;
                var videoTrack = sequence.videoTracks[0];
                
                // Find the imported project item by media path
                var importedItem3 = null;
                for (var j = 0; j < project.rootItem.children.numItems; j++) {
                    var item = project.rootItem.children[j];
                    if (item.getMediaPath && item.getMediaPath().replace(/\\/g, "\\") === path3) {
                        importedItem3 = item;
                        break;
                    }
                }
                
                if (importedItem3) {
                    videoTrack.overwriteClip(importedItem3, 6.0);
                } else {
                    // Fallback to index if path matching fails
                    videoTrack.overwriteClip(project.rootItem.children[project.rootItem.children.numItems - 1], 6.0);
                }
            } catch (err) {
                // Ignore and continue next clip
            }
            
        
        app.broadcastMessage("Jarvis: Sequence Complete");
        