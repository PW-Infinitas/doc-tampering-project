This is just a quick note for myself
1. Maybe should run multiple times for each prompt*model*image with logging -> next is to try other batches with scanned docs + white background only (Use V2 to slowly polish)
2. Communicate: Confirm how many models (their codes) do I acc have access to + Is my synthetic data reasonable -> yes but try payslip and try to imitate the most common case more


4. Augment images to expand negative case space
5. Synthesize more tampered images, following the plan
6. Finalise the model list, prompt list, image list -> Run the script a few times for each and log all
7. Analyse the results.


Note for prompt improvements:
1. Scope Expansion: Changed "whether any text" to "whether any text or its immediate background". This forces the model to treat the background immediately surrounding the text as part of the text element being verified.
2. Background Baseline: Added instructions to establish a "background baseline" (which will almost always be white/uniform in these docs).
3. Strong Signal Override: Appended "...but treat glaring visual anomalies (such as brightly colored overlays) as definitive strong signals" to prevent the model from dismissing colored boxes due to the "single weak signal" rule.
4. Explicit Target Descriptions: Added "superimposed bounding boxes, highlights, or opaque colored overlays" directly to the bulleted list of what to look for.
5. New Signal Type: Added background_overlay to the list of acceptable signal_type values in the JSON schema so the model has a specific category to bucket these anomalies into.
