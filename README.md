# WIP 90% done

i have been trying to make a small pdf to markdown pipeline which does the following - 1. convert all pages to images 2. get markdown from images, ask to place <image_here> tag when it finds diagrams, images etc. 3. do a second pass and just ask the llm to get bounding boxes. parse boxes and replace <image_here> with the coordinates.  4. extract image, store it, replace bbox with relative path in the markdown

gemini flash kinda sucks in identify diagrams/figures. it also hallucinates in bbox formatting sometimes.

gpt4o and gemini pro 1.5 did much better. i am still not satisfied with there bbox coordinate performance (looks like pro is slightly better than gpt4o here)

i am also not sure gpt4o normalised coordinates to 1000, 1000 like gemini does.

overall brain fried by this simple activity