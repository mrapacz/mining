# mining

## Setup
Installing dependencies:
```bash
pip install -r requirements.txt
```

## Gephi
In order to visualize computed betweenness centrality in Gephi use `*.gml` files
You may also try loading `ed_plot.gephi`, though it will probably not work because of differing paths between systems.

## Recomputing .gml files
In case you wanted to recompute one of the .gml files.

1. Specify, which file you want to use as input dataset
```python
MAP_FILE: str = SMALL_KRK 
# or
MAP_FILE: str = KRK
```

2. Run the computations
```bash
python main.py
```
