# python3 - Flexible Job shop planning for real-life HSP applications. Full implementation. Tornado server with client interface provided. With animations and Gantt diagrams.
### Custom NSGA-II operators + modified Shifting bottleneck heuristic (using branch and bound, EDD rule)
### Solves the conflicts problem of multiple cranes over single bath. Paralell computation using processes. 
Problem: FJc | no-wait, block | Cmax (minimization of production time, very constrained optimization problem with blocking and no-wait constraints).

Python3 working concept. Needs to be rewritten to C++. I do not have time for that.

## native

python3 -m venv venvdir

source venvdir/bin/activate

cd aplikace

python -m pip install -r Requirements.txt

python server.py


## docker
cd aplikace

sudo docker build -t rp .

sudo docker run -p 8888:8888 --rm rp

## Special thanks to Christelle Bloch, pymoo guy, networkx team and VUT Brno CZ.

