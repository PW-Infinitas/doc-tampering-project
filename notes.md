## This is just a quick note for myself
1. Maybe should run multiple times for each prompt*model*image with logging -> next is to try other batches with scanned docs + white background only (Use V2 to slowly polish)
2. Communicate: Confirm how many models (their codes) do I acc have access to + Is my synthetic data reasonable 


4. Augment images to expand negative case space & can do this while running smth in the background
5. Synthesize more tampered images, following the plan (wait for the printed docs)
6. Finalise the model list, prompt list, image list -> Run the script a few times for each and log all
7. Analyse the results.

### Work loop for today
- Get ready for looping through the models, temps, prompt versions for each image
- Analyse whatever I can in the meantime -> improve my prompts/ cut down some cases 

- Augmentation study + script EOD


### Signal type definitions (what each one means / what edit it points to):
1. font_weight_inconsistency - a value (e.g. an amount) is bolder or lighter than other values of the same field type elsewhere in the doc. Usually means the number was retyped/replaced and the new text was set in a different font weight than the original template.
2. resolution_mismatch - the edited text looks sharper or blurrier (different pixel density) than the rest of the document. Happens when an edited region is a pasted-in image/screenshot rendered at a different DPI, then composited back in.
3. baseline_mismatch - the text doesn't sit on the same horizontal line as surrounding text in the same row/column. Suggests the text box was repositioned (shifted up/down) when the value was swapped in.
4. shadow_edge_anomaly - faint shadows, halos, or jagged/soft edges around a text region that the rest of the document doesn't have. A telltale sign of a layer/box pasted on top of the original background.
5. color_contrast_discontinuity - the text or its background has a slightly different color/contrast than the surrounding area (e.g. off-white patch on a white background). Often the residue of covering the original value with a patch before writing the new one.
6. font_size_mismatch - the font size of a value differs from other values of the same field type (e.g. one amount noticeably bigger/smaller than the rest). Indicates the replacement text wasn't set to match the original template's font size.
7. background_overlay - an opaque colored box, highlight, or overlay placed over part of the document, typically to hide/cover original content. The most "obvious" tamper signal - a visible rectangle or block of color where it doesn't belong.
8. other - catch-all for any tampering signal that doesn't fit the categories above (gives the model somewhere to put genuine anomalies it can't otherwise classify).


## Decision log:
- label / label_signals (ground truth): NOT stored in results_log.jsonl. Kept in image_labels.json (keyed by image_path) and joined into the DataFrame by load_results() at load time, same way verdict/confidence/signal_types/format are derived from parsed_response. Reason: keeps the raw log untouched (append-only, true record of what was logged), and lets corrections to image_labels.json apply retroactively to old rows without any backfill/migration.

- This means: I decided to store the responses in results_log.jsonl and image_labels.json separately








Recommended parameter (by Gemini) is   --parameters='temperature=0.1,maxOutputTokens=2048,topP=0.95,topK=40'.