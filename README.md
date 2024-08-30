# 🐴 Horsin around
***Minecraft horse breeding management: scoring high on multiple objectives in a stochastic game***

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
2. A Google Sheets file for keeping track of horse stats
3. A system for having the Sheet call Python code to recommend horse management moves:
    - Killing and moving around horses after a round of breeding, to drop low quality horses (and always keep the same number of horses)
    - Reordering the horses, to make sure we breed high quality horses with other high quality horses

❗ Step (3) is the tricky one, and I ended up doing the following:
1. The Sheet calling a [Script extension](https://www.google.com/script/start/) (find it via Google Sheets -> Extensions -> Apps script)
2. That Script extension JavaScript following [this StackOverflow answer](https://stackoverflow.com/a/22933777) to make url requests
3. A [Google Cloud](https://cloud.google.com/) service running the code in this repo to process the requests

<mark>**So this code is designed to run on a Google Cloud service with their Python buildpack, using a Flask app to handle url requests.**</mark> Google Cloud's free options were enough for me to get the job done.

Once that link is set up (of the main Sheet calling Python), that gives lots of flexibility to play around with the management logic. Right now I have it
- Ranking horses, according to
  - [Pareto efficiency](https://en.wikipedia.org/wiki/Pareto_efficiency)
  - Total value of the horse's stats
  - "Centrality" of the horse (favoring a horse with 80% speed and 80% jump over a horse with 85% speed and 75% jump)
  - Tiebreaks on the values of the stats
- Writing out instructions for the kill/move steps after a round of breeding
- Writing out instructions for the move steps during a reordering

The system is flexibile about which stats you want to optimize: for example, I'm largely ignoring health and just optimizing speed and jump but I could just pass the url fetch all three stats as "primaries" to optimize them all.

📔 I really enjoying setting this up, since at the start I had no experience with Google Apps Scripts or Google Cloud. So it was a lot of learning, and there's a lot I still don't know (like what the url requests I'm relying on actually are! and how general these requests are: it looks like they build websites?...). This is definitely turning me towards learning more "backend" things like cloud management and how to make websites and apps with Python. But also I feel like I learned a lot about creating a framework for handling a complex problem in a user-friendly way: Google Sheets for ease of interaction, Python for ease of coding, and the "rank then decide" framework for giving the user visiblity into the decision process. Solutions to problems like this one could get arbitrarily complex, and my Python backend gives the ability to introduce a lot of complexity. But despite that, the duo of a simple in-game setup (of a fixed number of horses tied to fenceposts) and the easy-to-interact-with management system (Google Sheets) manages to keep everything transparent and organized.

🥉 Lastly: the code is pretty low-tech, but I'd recommend Python version 3.6+ to ensure a (non-critical) part works correctly (a step that tidies instructions by relying on dictionaries preserving insertion order).
