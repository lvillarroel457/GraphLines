def nx_to_dict(G):

    '''
    Recibe un grafo o digrafo de networkx con pesos y retorna un diccionario con 2 llaves; 'nodes' y 'edges'.
    El valor de 'nodes' es la cantidad de nodos del grafo. 
    El valor de 'edges' es una lista con todas las aristas o arcos en forma de tuplas de tamaño 3. El tercer elemento de la tupla es el peso. Si el grafo es dirigido la dirección es de izuierda a derecha.
    
    '''
    
    
    edges = [(e[0], e[1], e[2]['weight']) for e in G.edges(data=True)] 
    dict = {'nodes': len(G.nodes()), 'edges': edges}
    
    return dict
    


def g_dict_to_nx(dict):

    '''

    Recibe un diccionario en el formato entregado por la función nx_to_dict().
    Retorna un grafo de networkx correspondiente con el diccionario.
    
    '''
    
    n = dict['nodes']
    edges = dict['edges']
    
    G = nx.Graph()
    
    G.add_nodes_from(range(n))
    G.add_weighted_edges_from(edges)

    return G


def d_dict_to_nx(dict):

    '''

    Recibe un diccionario en el formato entregado por la función nx_to_dict().
    Retorna un digrafo de networkx correspondiente con el diccionario.
    
    '''
    
    n = dict['nodes']
    edges = dict['edges']
    
    G = nx.DiGraph()
    
    G.add_nodes_from(range(n))
    G.add_weighted_edges_from(edges)

    return G
        


def weighted_edges_input(input):
    '''
    Recibe un string (input) de la forma '2-4:4, 1-3, 4-5:2', el cual se interpreta de la siguiente forma. El string corresponde a aristas separadas por comas.
    Dentro de una arista, primero están los dos nodos separados por un '-', luego hay ':' y finalmente el peso de la arista. Si no hay peso, se asigna peso 1.
    'u-v:k' representa la arista (u,v) con peso k. 'u-v' representa la arista (u,v) con peso 1. 
    En el caso no dirigido la dirección se ingnora por la librería networkx. En el caso dirigido la dirección de la arista es de izquierda a derecha.
    Tanto u como v como k deben ser números naturales.
    
    Retorna las aristas como tuplas de tamaño 3 en una lista, formato con el que se usa G.add_weighted_edges_from() de networkx.
    El tercer elemento de la tupla representa el peso.

    Por ejemplo, weighted_edges_input('2-4:4, 1-3, 5-4:2') retorna [(2,4,4), (1,3,1), (5,4,2)]
    
    '''
    L1 = input.split(',')
    L2 = [tuple(wedge.split(':')) for wedge in L1]
    L3 = []
    for wedge in L2:
        if len(wedge)==1: #No hay peso
            L3.append(tuple([int(v) for v in wedge[0].split('-')]+[1])) #Se pone peso 1 
        elif len(wedge)==2: #Hay peso
            L3.append(tuple([int(v) for v in wedge[0].split('-')]+[int(wedge[1])]))

        else:
            raise Exception("Error en el input")

    return L3


def remove_edges_process(input):

    '''
    Recibe un string (input) de la forma '2-3, 4-0, 5-6', el cual corresponde a aristas separadas por comas.
    'u-v' representa la arista (u,v). Tanto u como v deben ser números naturales.
    En el caso no dirigido, la dirección se ignora por la librería networkx. En el caso dirigido la dirección de la arista es de izquierda a derecha.

    Retorna las aristas como tuplas de tamaño 2 en una lista, formato con el que se usa G.remove_edges_from() de networkx.

    Por ejemplo, remove_edges_process('2-3, 4-0, 5-6') retorna [(2,3), (4,0), (5,6)]
    
    '''
    

    
    edges = [tuple([int(v) for v in edge.split('-')]) for edge in input.split(',')]
    
    return edges


def remove_vertices_process(input):

    '''
    
    Recibe un string (input) de la forma '2, 0, 5', el cual corresponde a vértices separados por comas. Los vertices deben ser números naturales.

    Retorna los vértices como enteros en una lista, formato con el que se usa G.remove_nodes_from() de networkx.

    Por ejemplo, remove_edges_process('2, 0, 5') retorna [2,0,5]
    
    '''
    

    vertices = [int(v) for v in input.split(',')]
    
    return vertices


def nx_to_cytoscape_elements(G):

    '''

    Recibe un grafo de networkx y retorna el argumento elements correspondiente al grafo en el formato que usa la cytoscape de dash.
    
    '''

    elements = [
            {"data": {"id": str(node), "label": str(node)}} for node in G.nodes()
        ] + [
            {"data": {"source": str(edge[0]), "target": str(edge[1]), "weight": str(G[edge[0]][edge[1]]['weight'])}} for edge in G.edges()
        ] 
    return elements