# 🐴 Horsin' around
***Minecraft horse breeding management: scoring high on multiple objectives via selection***

See [main.py](https://github.com/nicolas-bolle/horsin-around/blob/main/main.py) for the Flask app this repo runs and the functions it calls for the core processing. See [spreadsheet.pdf](https://github.com/nicolas-bolle/horsin-around/blob/main/spreadsheet.pdf) for a view of the front end I set up for the system.

There are a lot of possible horses in Minecraft:
![image](https://github.com/user-attachments/assets/f8ba401a-155a-4ffb-ae82-a4619248d5ed)

But separate from color/pattern, there are the three [equine stats](https://minecraft.fandom.com/wiki/Horse#Statistics):
- ❤️ Health: the hitpoints of the horse, from 7.5 to 15 hearts
- 🐇 Speed: how fast the horse can run, from 4.7 to 14.2 blocks per second
- 🦘 Jump: how many blocks the horse can jump vertically, from 1.1 to 5.3 blocks

It's not feasible to get a perfect horse (bringing each stat to 100%), but selective breeding and some patience can help get a good quality steed.

This makes for an interesting problem: breeding to produce a good horse in these multiple objectives, ideally in a relatively low number of generations and with minimal headache. It's a complex problem: multiple variables, probabilistic evolution over time, and the whole management angle of juggling horse stats and the actual horses without it getting overwhelming. So we want a good strategy for tackling this, and a flexible backend system to support it.

*Sidenote: figuring out the stats of a horse in vanilla Minecraft is an ordeal of its own...health is easy, but jump and speed require building contraptions to help do the measuring. That takes time, and there's also potential for measurement error. So we can cut out the less fun part by using [this datapack](https://modrinth.com/datapack/horses-genetic), which displays horse stats as percentages. This code is written with the assumption that horse stats are passed in this normalized form, with a max value of 1 (so if you use a manual measuring approach, make sure to normalize before passing things into the Python!).*

💻 Here's the system I settled on:
1. In game: a zone of labled fenceposts to tie the adult horses to, and a second zone for the children after breeding
2. System frontend: a Google Sheets file for keeping track of horse stats
3. System backend: something running Python code to recommend horse management moves:
    - Killing and moving around horses after a round of breeding, to drop low quality horses (and always keep the same number of horses)
    - Reordering the horses, to make sure we breed high quality horses with other high quality horses

❗ Linking steps 2 and 3 was the hard part, since it was my first time setting up cloud computing, URL requests, and a Flask web app. Here's what I did:
1. The Sheet calls a [Script extension](https://www.google.com/script/start/) (find it via Google Sheets -> Extensions -> Apps script) via buttons
2. That Script extension follows [this StackOverflow answer](https://stackoverflow.com/a/22933777) to make URL requests
3. A [Google Cloud](https://cloud.google.com/) service runs the code in this repo to receive and process the requests

<mark>**So this code is designed to run on a Google Cloud service with their Python buildpack.**</mark> Google Cloud's free options were enough for me to get the job done, since the service runs serverless and I needed minimal resources. I also built in some barebones security, requiring the user to know a password (that I stored away as a Google Cloud secret) for me to process their request.

Once that link is set up (of the frontend Sheet calling the backend Python), that gives lots of flexibility to play around with the management logic. Right now I have it
- Ranking horses, according to
  - [Pareto efficiency](https://en.wikipedia.org/wiki/Pareto_efficiency)
  - Total value of the horse's stats
  - "Centrality" of the horse (favoring a horse with 80% speed and 80% jump over a horse with 85% speed and 75% jump)
  - Tiebreaks on the values of the stats
- Writing out instructions for the kill/move steps after a round of breeding
- Writing out instructions for the move steps during a reordering

The system is flexibile about which stats you want to optimize: for example, I'm largely ignoring health and just optimizing speed and jump but I could just pass the url fetch all three stats as "primaries" to optimize them all.

🌻 Here's a view of the frontend: [spreadsheet.pdf](https://github.com/nicolas-bolle/horsin-around/blob/main/spreadsheet.pdf). Users can edit the green outlined cells to enter in horse stats (while the rest of the sheet is protected). The buttons run scripts that call the Python backend and populate cells in the spreadsheet (the horse rankings and the human-readable instructions at the top right). Examples:
- Horse A is rank 2 among the current horses in Zone 1, but rank 5 if you include the children in Zone 2
- The reorg instructions result in horse K moving to slot A, since K is the highest ranked of the Zone 1 horses
- The merge instructions result in horses C (rank 21) and S (rank 23) being killed, since they underperform other horses and there's not enough room for them in Zone 1
- This wave of horse breeding improved our best horse from K (95% speed and 93% jump) to U (97% speed and 96% jump)!

📔 There was a lot of learning to do for this, since again I had never set up frontend/backend/requests. I used a qa server for testing during the early development, and when I finally got the URL requests to the backend working (with a simple "Hello, World!" and echoing the request payload) I still wasn't clear on what a URL request actually was! So next I'm working through getting a baseline understanding of internet/cloud/app specifics: stuff like the IP suite, APIs, Kubernetes, Flask, and finally learning Streamlit and Dash. There's also some light jank in this repo like [this function](https://github.com/nicolas-bolle/horsin-around/blob/13139ec3b3bf8ae194da1c37b94160fdc692b5f7/main.py#L20), which I'd like to clean up on the next project. My goal is to set up a website in the next few weeks: I have some HTML pages from grad school listing out projects I worked on, but it would be nice to start making web apps. Maybe there's a version of this horse management I can productionize: it could be cool to host a Minecraft horse management utility! Or gameify it a bit, like [this neat elevator programming game](https://play.elevatorsaga.com/). But at the very least, set up the infrastucture so I can pretty easily start deploying cool projects.

🥉 Last thing: the code is pretty low-tech, but I'd recommend Python version 3.6+ to ensure a (non-critical) part works correctly (a step that tidies instructions by relying on dictionaries preserving insertion order).
