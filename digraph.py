from dash import Dash, dcc, html, Input, Output, State, ctx
import dash_cytoscape as cyto
import networkx as nx
import numpy as np
import ast

from line_functions import FW, Betweenness, lines, matrixtolinesdict
from process_functions import nx_to_dict, d_dict_to_nx, weighted_edges_input, remove_edges_process, remove_vertices_process, nx_to_cytoscape_elements


app = Dash(__name__) #Se crea la aplicación

edge_style = [{'selector': 'edge', 'style': {'curve-style': 'bezier','target-arrow-shape': 'triangle'}}] #Hace que los arcos sean curvados y que tenga un triángulo en la cabeza del arco.

stylesheet = [{'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center','text-halign': 'center'}}] + edge_style #Hace que además se vea el 'label' de cada nodo en su centro.



app.layout = html.Div([
    html.Div(dcc.Store(id='graph-dict', data=[{'nodes': 0, 'edges': []}, {'nodes': 0, 'edges': []}])), #Lista de tamaño 2 donde cada elemento es un diccionario correspondiente a un grafo. El tamaño 2 es para la funcionalidad 'deshacer'. Ambas entradas inician con el diccionario del grafo vacío.
    html.Div(dcc.Store(id='graph-dict-counter', data=[0])), #Guarda la posición de graph-dict data en la que está el grafo que se está visualizando.
    html.Div(dcc.Store(id='undo-state', data=False)), #Si data=True, se puede deshacer, sino, no.
    html.Div(dcc.Store(id='selected-nodes', data=[])), #Lista para guardar los nodos seleccionados de forma interactiva para la visualización de las líneas o agregar aristas clickeando nodos.
    html.Div(dcc.Store(id='lines', data=[])), #Para guardar y actualizar las líneas.
    html.Div(dcc.Store(id='lines-state', data=False)), #Si data=True, las líneas están actualizadas, si data=False, no.
    html.Div(id='lines-info', children='', #Texto con información de las líneas.
                 style={
    'textAlign': 'left',
    'color': 'blue',
    'fontSize': 20,
    'whiteSpace': 'pre-wrap',  # Ensures wrapping and respects newlines
    'overflowWrap': 'break-word',  # Breaks long words to fit within the div
    'padding': '25px',  # Internal spacing
    'margin': '15px',   # External spacing
    'width': '92%',     # Adjust width
    'border': '1px solid lightgray',  # Optional: Add a border for clarity
    'borderRadius': '5px',  # Rounded corners for the border
    'boxShadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',  # Add a shadow for better aesthetics
    'backgroundColor': 'white',  # Background color for better contrast
    'lineHeight': '1.4',  # Adjust line height for better readability
    'minHeight': '160px',  # Ensure a minimum height for the div
    'overflowY': 'auto',  # Add scroll if the text overflows vertically
    'marginLeft': '20px'
    }),  

    html.Div(dcc.Checklist(["Pesos"], [], id="weight-checklist", inline=True), style={'display': 'inline-block', 'marginRight': '6px', 'marginLeft': '8px'}), #Checklist; si está seleccionada (['Pesos']), se muestran los pesos de las aristas, si no, no.
    html.Div(dcc.Checklist(["Fijar nodos"], [], id="pos-checklist", inline=True), style={'display': 'inline-block', 'marginRight': '8px'}), #Checklist; Si está seleccionada, la posición de los nodos queda fijada.
    html.Div(dcc.Checklist(["Modificar digrafo"], ["Modificar digrafo"], id="mod-checklist", inline=True), style={'display': 'inline-block', 'marginRight': '1px'}), #Checklist; Si está seleccionada, se pueden agregar aristas clickeando nodos, y se puede borrar aristas clickeándolas.
    html.Div(
        dcc.Input(id='clicked-edge-weight', type='text', placeholder="Ej: 3", style={'width': '80px'}, autoComplete='off'), #Input para agregar peso a una arista que se agrega al clickear nodos.
        style={'display': 'inline-block', 'marginRight': '4px','padding': '2px' }),  
    html.Div([
        dcc.Input(id='add-from-dict-input', type='text', placeholder="Formato de diccionario dado por descargar.", style={'width': '387px'}, autoComplete='off'), #Input para cargar un grafo desde un diccionario en el formato que usa la aplicación (y que está en descargar).
        html.Button("Cargar desde diccionario", id="add-from-dict-btn", n_clicks=0), #Botón para cargar desde diccionario.
    ], style={'display': 'inline-block', 'marginRight': '2px', 'marginLeft': '123px'}),     
    html.Div([
    html.Button("Deshacer", id="undo-btn",  n_clicks=0), #Botón para deshacer.
    ], style={'display': 'inline-block', 'marginLeft': '4px'}),
    html.Br(), 
    html.Div([
        dcc.Input(id='add-vertices-input', type='text', placeholder="Ej: 5", style={'width': '60px'}, autoComplete='off'), #Input para agregar vértices.
        html.Button("Agregar nodos", id="add-vertices-btn", n_clicks=0), #Botón para agregar vértices.
    ], style={'display': 'inline-block', 'marginRight': '2px', 'marginLeft': '10px'}), 
    html.Div([
        dcc.Input(id='add-edges-input', type='text', placeholder="Ej: 0-1, 3-5:4, 2-1", style={'width': '120px'}, autoComplete='off'), #Input para agregar aristas.
        html.Button("Agregar aristas", id="add-edges-btn", n_clicks=0), #Botón para agregar aristas.
    ], style={'display': 'inline-block', 'marginRight': '2px'}),
    html.Div([
        dcc.Input(id='remove-vertices-input', type='text', placeholder="Ej: 2,5,6", style={'width': '100px'}, autoComplete='off'), #Input para remover vértices.
        html.Button("Remover nodos", id="remove-vertices-btn", n_clicks=0), #Botón para remover vértices.
    ], style={'display': 'inline-block', 'marginRight': '2px'}),
    html.Div([
        dcc.Input(id='remove-edges-input', type='text', placeholder="Ej: 1-2, 4-3", style={'width': '120px'}, autoComplete='off'), #Input para remover aristas.
        html.Button("Remover aristas", id="remove-edges-btn", n_clicks=0), #Botón para remover aristas.
    ], style={'display': 'inline-block', 'marginRight': '4px'}),
    html.Div([html.Button("Borrar grafo", id="clear-graph-btn", n_clicks=0), #Botón para borrar el grafo.
    ], style={'display': 'inline-block', 'marginRight': '4px'}),                    
    html.Div([html.Button("Actualizar líneas", id="lines-btn", n_clicks=0), #Botón para actualizar las líneas.
    ], style={'display': 'inline-block'}),
                        
    html.Div(id='lines-state-info', children='', style={'display': 'inline-block', 'marginLeft': '6px', 'minWidth': '220px'}), #Texto con información sobre el estado de las líneas.
    html.Div([
    html.Button("Descargar", id="download-btn"), #Botón para descargar información.
    dcc.Download(id="download-info")
], style={'display': 'inline-block', 'marginLeft': '4px'}),

    #Gafo de cytoscape
    cyto.Cytoscape( 
        id='graph',
        elements=[],
        stylesheet=stylesheet,
        layout={'name': 'cose'},  
        style={'width': '100%', 'height': '500px'} 
    )
])

# Callback 1: Edición del grafo
@app.callback(
    Output('undo-state', 'data', allow_duplicate=True),  #Nuevo valor de 'data' para el id 'undo-state'. Esto es análogo para todos los demas inputs. allow_duplicate=True es porque hay otros callbacks con el mismo output.
    Output('graph-dict', 'data', allow_duplicate=True),
    Output('graph-dict-counter', 'data', allow_duplicate=True),
    Output('graph', 'elements', allow_duplicate=True),
    Output('lines-state-info', 'children', allow_duplicate=True), #Children es el mensaje que se muestra
    Output('lines-state', 'data', allow_duplicate=True),
    Output('lines-info', 'children', allow_duplicate=True),
    Output('graph', 'stylesheet', allow_duplicate=True),
    Output('graph', 'layout', allow_duplicate=True),
    Output("pos-checklist", "value"), # Nuevo valor del checklist con id 'pos-checklist'. Si es ['Fijar nodos'] se marca el checklist, si es [] queda desmarcado.
    Output('add-vertices-input', 'value'), #Nuevo valor del input asociado al id 'add-vertices-input'. El string que se retorne se verá en la casilla del input. Esto es análogo para los demás.
    Output('add-edges-input', 'value'),
    Output('remove-vertices-input', 'value'),
    Output('remove-edges-input', 'value'),
    Output('add-from-dict-input', 'value'),
    Output('selected-nodes', 'data', allow_duplicate=True),
    Input('graph', 'tapEdgeData'), #Esto hace que se active el callback a clickear una arista
    Input('add-vertices-btn', 'n_clicks'), #Esto hace que se active el callback a clickear el botón con id 'add-vertices-btn'. Esto es análogo para los demás.
    Input('add-edges-btn', 'n_clicks'),
    Input('remove-vertices-btn', 'n_clicks'),
    Input('remove-edges-btn', 'n_clicks'), 
    Input('clear-graph-btn', 'n_clicks'), 
    Input('add-from-dict-btn', 'n_clicks'),
    Input('add-vertices-input', 'n_submit'), #Esto hace que se active el callback a apretar 'enter' en el input con id 'add-vertices-input'. Esto es análogo para los demás.
    Input('add-edges-input', 'n_submit'),
    Input('remove-vertices-input', 'n_submit'),
    Input('remove-edges-input', 'n_submit'),
    Input('add-from-dict-input', 'n_submit'),
    State('add-vertices-input', 'value'), #La variable asociada en el argumento de la función será el string (valor) actual correspondiente a lo que está escrito en el input con id 'add-vertices-input'. Esto es análogo para los demás.
    State('add-edges-input', 'value'),
    State('remove-vertices-input', 'value'),
    State('remove-edges-input', 'value'),
    State('add-from-dict-input', 'value'),
    State("weight-checklist", "value"), #La variable asociada en el argumento de la función será una la lista ['Pesos'] si el checklist está seleccionado o será la lista [] si no. Esto es análogo para los demás.
    State("pos-checklist", "value"),
    State('lines-state', 'data'), #La variable asociada en el argumento de la función será el valor de 'data' correspondiente al id 'lines-state'. Esto es análogo para los demás.
    State('graph-dict', 'data'),
    State('graph-dict-counter', 'data'),
    State('undo-state', 'data'),
    State("mod-checklist", "value"),
    prevent_initial_call=True #Esto hace que no se ejecute el callback al iniciar la aplicación. Esto es necesario pues el callback tiene allow_duplicate=True. De otra forma habría un error.
)
def update_graph(tapped_edge_data, add_v_clicks, add_e_clicks, remove_v_clicks, remove_e_clicks, clear_g_clicks, add_from_dict_clicks,
                 add_v_submit, add_e_submit, remove_v_submit, remove_e_submit, add_from_dict_submit,
                 add_vertices_input, add_edges_input, remove_vertices_input, remove_edges_input, add_from_dict_input, weights, position, lines_state, graph_dict, graph_dict_counter, undo_state, modify):


    i = graph_dict_counter[0] #i es la posición de graph_dict en la que se encuentra el grafo que se está visualizando.
    g_dict = graph_dict[i] #g_dict es el diccionario asociado al grafo que se está visualizando.
    G = d_dict_to_nx(g_dict) #G es grafo que se está visualizando (en netwrokx).

    #Por defecto se mantienen las siguientes variables, lo cual sirve por ejemplo si se ejecuta el callback de forma inútil (como un input vacío).

    new_undo_state = undo_state 
    new_i = i
    
    new_pos = position
    
    new_add_vertices_input = add_vertices_input
    new_add_edges_input = add_edges_input
    new_remove_vertices_input = remove_vertices_input
    new_remove_edges_input = remove_edges_input
    new_add_from_dict_input = add_from_dict_input

    new_selected_nodes = [] #Se desseleccionan los nodos

    if weights: #Si está seleccionado Pesos en el checklist
        
        edge_style = [{'selector': 'edge', 'style': {'label': 'data(weight)', 'text-background-color': 'white',
                    'text-background-opacity': 0.8, 'curve-style': 'bezier','target-arrow-shape': 'triangle'}}]
        

    else:

        edge_style = [{'selector': 'edge', 'style': {'curve-style': 'bezier','target-arrow-shape': 'triangle'}}]



    layout={'name': 'preset', 'fit': False} #Con este layout se mantiene todo fijo, y está por defecto por si se ejecuta el callback de forma inútil.


    triggered_id = ctx.triggered_id #Corresponde al id del input que disparó el callback
    
    message1 = ''
    message2 = ''

    new_lines_state = lines_state #Por defecto se mantiene el lines_state


    stylesheet = [
            {'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center',
                        'text-halign': 'center'}}
        ] + edge_style # Para que al modificar al grafo se deje de ver una línea si es que está destacada
    
    
    if (triggered_id == 'add-vertices-btn' or triggered_id == 'add-vertices-input') and add_vertices_input: #Esta cláusula es falsa si add_vertices_input es vacío. Esto es análogo para los demás.

        #Los comentarios de esta parte son análogos en todas, por lo que solo se comentará este.
        try:
            vertices = int(add_vertices_input)

            assert (vertices > 0) 

            n = len(G.nodes())
            G.add_nodes_from(range(n, n + vertices)) #Se agregan 'vertices' nodos en orden partiendo desde n
            
            message1 = 'Líneas no actualizadas.'

            new_lines_state = False

            new_add_vertices_input = '' #Si funciona, el input se borra.

            if not position: #Si no está marcada la checklist de fijar digrafo.
                
                layout={'name': 'cose'}

            new_undo_state = True #Se puede deshacer. 
            new_i = (i+1)%2  #new_i será la posición en el en la lista graph_dict donde será guardado el diccionario del grafo modificado. La otra posición (i) mantendrá el diccionario del grafo anterior, lo que permitirá volver al grafo anterior con el botón de 'deshacer'.   

        except: #Hubo un error

            message2 = 'Error en el input. Intente de nuevo.'

            
        
    elif (triggered_id == 'add-edges-btn' or triggered_id == 'add-edges-input' ) and add_edges_input:

        try:

            edges = weighted_edges_input(add_edges_input)    
            G.add_weighted_edges_from(edges)
    
    
            mapping = {j: i for i, j in enumerate(G.nodes())} #Permutación para ordenar los vértices que pueden no estar en orden por ejemplo si se agrega la arista 4-3 sin que estén previamente los nodos 3 y 4 en el grafo.
            G = nx.relabel_nodes(G, mapping) 
    
            message1 =  'Líneas no actualizadas.'

            new_lines_state = False

            new_add_edges_input = ''

            
            if not position:
                
                layout={'name': 'cose'}

            new_undo_state = True 
            new_i = (i+1)%2      

        except:

            message2 = 'Error en el input. Intente de nuevo.'
            
            
        
    elif (triggered_id == 'remove-vertices-btn' or triggered_id == 'remove-vertices-input') and remove_vertices_input:


        try:
        
            vertices = remove_vertices_process(remove_vertices_input)
            
            G.remove_nodes_from(vertices)
            mapping = {j: i for i, j in enumerate(G.nodes())} #Permutación para ordenar los vértices si es que no se quitan solo los últimos vértices.
            G = nx.relabel_nodes(G, mapping) 
    
            message1 = 'Líneas no actualizadas.'

            new_lines_state = False

            new_remove_vertices_input = ''


            if not position:
                
                layout={'name': 'cose'}

            new_undo_state = True 
            new_i = (i+1)%2      


        except:
            
            message2 = 'Error en el input. Intente de nuevo.'



        
    elif (triggered_id == 'remove-edges-btn' or triggered_id == 'remove-edges-input') and remove_edges_input:


        try: 
            
            edges = remove_edges_process(remove_edges_input)
            G.remove_edges_from(edges)
            message1 = 'Líneas no actualizadas.'

            new_lines_state = False


            new_remove_edges_input = ''


            if not position:
                
                layout={'name': 'cose'}

            new_undo_state = True
            new_i = (i+1)%2       

        except:

            message2 = 'Error en el input. Intente de nuevo.'

        
    elif (triggered_id == 'add-from-dict-btn' or triggered_id == 'add-from-dict-input') and add_from_dict_input:

        try:

            G2 = d_dict_to_nx(ast.literal_eval(add_from_dict_input))
            G = nx.DiGraph(G2)

            message1 = 'Líneas no actualizadas.'

            new_lines_state = False

            new_add_from_dict_input = ''

            if not position:
                
                layout={'name': 'cose'}


            new_undo_state = True
            new_i = (i+1)%2   

        except:

            message2 = 'Error en el input. Intente de nuevo.'


    elif triggered_id == 'clear-graph-btn':
        G.clear()
        message1 = ''

        new_lines_state = False

        new_pos = []


        new_add_vertices_input = ''
        new_add_edges_input = ''
        new_remove_vertices_input = ''
        new_remove_edges_input = ''


        new_undo_state = True 
        new_i = (i+1)%2  


    elif triggered_id == 'graph':

        if modify: #Está marcado el checklist de modificar digrafo

            u = int(tapped_edge_data['source'])   
            v = int(tapped_edge_data['target'])   
            G.remove_edges_from([(u,v)])  

            message1 = 'Líneas no actualizadas.'

            new_lines_state = False

            new_undo_state = True
            new_i = (i+1)%2  

    
    
    elements = nx_to_cytoscape_elements(G) #Esto es lo que se visualizará

    new_graph_dict_counter = graph_dict_counter
    new_graph_dict_counter[0] = new_i #La nueva posición del grafo en la lista
    new_g_dict = nx_to_dict(G)
    new_graph_dict = graph_dict
    new_graph_dict[new_i] = new_g_dict #Se guarda el diccionario en la nueva posición

    
    return new_undo_state, new_graph_dict, new_graph_dict_counter, elements, message1, new_lines_state,  message2, stylesheet, layout, new_pos, new_add_vertices_input, new_add_edges_input, new_remove_vertices_input, new_remove_edges_input, new_add_from_dict_input, new_selected_nodes




#Callback 2: Deshacer
@app.callback(
        Output('undo-state', 'data', allow_duplicate=True), 
        Output('graph', 'elements', allow_duplicate=True),
        Output('graph-dict-counter', 'data', allow_duplicate=True),
        Output('lines-state-info', 'children', allow_duplicate=True),
        Output('lines-state', 'data', allow_duplicate=True),
        Output('lines-info', 'children', allow_duplicate=True),
        Output('graph', 'layout', allow_duplicate=True),
        Output('graph', 'stylesheet', allow_duplicate=True),
        Input('undo-btn', 'n_clicks'),
        State('graph-dict', 'data'),
        State('graph-dict-counter', 'data'),
        State('undo-state', 'data'),
        State('lines-state', 'data'),
        State("pos-checklist", "value"),
        State("weight-checklist", "value"),
        prevent_initial_call=True,
        )
def undo_func(undo_clicks, graph_dict, graph_dict_counter, undo_state, lines_state, position, weights):


    if weights: #Si está seleccionado Pesos en el checklist
        
        edge_style = [{'selector': 'edge', 'style': {'label': 'data(weight)', 'text-background-color': 'white',
                    'text-background-opacity': 0.8, 'curve-style': 'bezier','target-arrow-shape': 'triangle'}}]
        

    else:

        edge_style = [{'selector': 'edge', 'style': {'curve-style': 'bezier','target-arrow-shape': 'triangle'}}]


    stylesheet = [
            {'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center',
                        'text-halign': 'center'}}
        ] + edge_style # Para que al modificar al grafo se deje de ver una línea si es que está destacada    


    if position: #Si está marcada la checklist de fijar digrafo.

        layout={'name': 'preset', 'fit': False}
            

    else:

        layout={'name': 'cose'}


    message2 = ''

    new_undo_state = False #Si se podía deshacer, ahora ya no se puede. Como la lista de los diccionarios es de tamaño 2, solo se puede deshacer una vez.

    if undo_state: #Si se puede deshacer

        i = graph_dict_counter[0] #i es la posición de la lista de graph_dict en la que está el grafo que se está visualizando
        new_i = (i-1)%2  #new_i es será la posición del otro grafo en la lista de graph_dict, es decir el anterior al que se está accediendo ahora con la funcionalidad de deshacer.
        g_dict = graph_dict[new_i]
        G = d_dict_to_nx(g_dict) #G es el grafo anterior al que se está accediendo

        

        elements = nx_to_cytoscape_elements(G)

        new_graph_dict_counter = graph_dict_counter
        new_graph_dict_counter[0] = new_i #Se actualiza el contador

        message1 = 'Líneas no actualizadas.'
        new_lines_state = False

    else: #No se puede deshacer, en este caso, se mantiene todo igual.

        i = graph_dict_counter[0]
        g_dict = graph_dict[i]
        G = d_dict_to_nx(g_dict)

        

        elements = nx_to_cytoscape_elements(G)

        new_graph_dict_counter = graph_dict_counter

        new_lines_state = lines_state

        if lines_state:

            message1 = 'Líneas actualizadas.'

        else:

            message1 = 'Líneas no actualizadas.'    




    return new_undo_state, elements, new_graph_dict_counter, message1, new_lines_state,  message2, layout, stylesheet 


# Callback 3: Pesos
@app.callback(
    Output('graph', 'stylesheet', allow_duplicate=True),
    Output('lines-info', 'children', allow_duplicate=True),
    Input("weight-checklist", "value"), #Se activa al apretar la checklist (ya sea para marcar o desmarcar)
    prevent_initial_call=True
)
def weight_checklists(weights):

    
    if weights: #Checklist marcado
        
        edge_style = [{'selector': 'edge', 'style': {'label': 'data(weight)', 'text-background-color': 'white',
                    'text-background-opacity': 0.8, 'curve-style': 'bezier','target-arrow-shape': 'triangle'}}]

    else: #Checklist no marcado
        
        edge_style = [{'selector': 'edge', 'style': {'curve-style': 'bezier','target-arrow-shape': 'triangle'}}]


    stylesheet = [
        {'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center',
                    'text-halign': 'center'}}
        ] + edge_style
    
    message2 = ''

    return stylesheet, message2

    


# Callback 4: Calcular líneas
@app.callback(
    Output('lines', 'data'),
    Output('lines-state-info', 'children', allow_duplicate=True),
    Output('lines-state', 'data', allow_duplicate=True),
    Output('lines-info', 'children', allow_duplicate=True),
    Output('selected-nodes', 'data', allow_duplicate=True),
    Input('lines-btn', 'n_clicks'),
    State('lines', 'data'),
    State('lines-state', 'data'),
    State('graph-dict', 'data'),
    State('graph-dict-counter', 'data'),
    prevent_initial_call=True
)
def calculate_lines(lines_click, lines_data, lines_state, graph_dict, graph_dict_counter):


    i = graph_dict_counter[0]
    g_dict = graph_dict[i]
    G = d_dict_to_nx(g_dict)

    triggered_id = ctx.triggered_id

    message1= ''
    message2= ''

    
    if triggered_id == 'lines-btn': #Es True siempre, se podría quitar este if.

        new_selected_nodes=[] #Se desseleccionan los nodos seleccionados.
        
        if len(G.nodes()) == 0:
            
            message1 = 'El grafo es vacío.'
            message2= ''

            new_lines_data = []

            new_lines_state=False
            
            

        elif not nx.is_strongly_connected(G):
            
            message1 = 'Grafo no fuertemente conexo.'
            message2= ''

            new_lines_data = []

            new_lines_state=False

            
        
        elif not lines_state: #Si no están calculadas las líneas
           
            n = len(G.nodes()) #Cantidad de nodos
            D = FW(G) #Matriz de distancias
            B = Betweenness(D) #Se calcula la bewteennness
            LM = lines(B, n) #Se calculan las líneas
            pairdict, linedict, l = matrixtolinesdict(LM, n) #Se calculan los diccionarios de las líneas 
            d = nx.diameter(G, weight='weight') #Se calcula el diámetro
            strD = np.array2string(D, separator=', ') #String de la matriz de distancias
            strB = str(B) #String con la bewteenness
            new_lines_data = [pairdict, linedict, l, d, n, strD, strB] #Se actualizan las líneas

            
            if l == n:
                lstr = 'Sí' #Hay línea universal
            else:
                lstr = 'No' #No hay línea universal
                      
            message1 =  'Líneas actualizadas.' 
            message2= 'Cantidad de líneas: '+ str(len(linedict.keys())) + '. Línea universal: ' + lstr + '. Diámetro: ' + str(d) +  '.\n' + 'No hay nodos seleccionados.'

            new_lines_state=True
            
        else: #line_state=True

            assert lines_state

            new_lines_data = lines_data #Se mantienen las líneas

            #Se accede a la información de las líneas para ponerla en el mensaje2

            pairdict =  lines_data[0]
            linedict = lines_data[1]
            l = lines_data[2]
            d = lines_data[3]
            n = lines_data[4]

            if l == n:
                lstr = 'Sí' #Hay línea universal
            else:
                 lstr = 'No' #No hay línea universal
                   
            message1 =  'Líneas ya actualizadas.' 
            
            message2= 'Cantidad de líneas: '+ str(len(linedict.keys())) + '. Línea universal: ' + lstr + '. Diámetro: ' + str(d) + '.\n' + 'No hay nodos seleccionados.'

            new_lines_state = lines_state
    
        

    return new_lines_data, message1, new_lines_state, message2, new_selected_nodes
        


# Callback 5: Modificar
@app.callback(
    Output('selected-nodes', 'data', allow_duplicate=True),
    Output('lines-info', 'children', allow_duplicate=True),
    Input("mod-checklist", "value"), #Se activa al apretar la checklist (ya sea para marcar o desmarcar)
    prevent_initial_call=True
)
def mod_checklists(modify):


    if modify:
        
        message = 'Seleccione 2 nodos para agregar la arista correspondiente.'

    else:

        message = ''

    new_selected_nodes=[]    

    return new_selected_nodes, message    







# Callback 6: Visualización de las líneas
@app.callback(
    Output('undo-state', 'data', allow_duplicate=True),    
    Output('graph-dict', 'data', allow_duplicate=True),
    Output('graph-dict-counter', 'data', allow_duplicate=True),
    Output('graph', 'elements', allow_duplicate=True),
    Output('graph', 'layout', allow_duplicate=True),    
    Output('graph', 'stylesheet', allow_duplicate=True),
    Output('lines-info', 'children', allow_duplicate=True),
    Output('selected-nodes', 'data', allow_duplicate=True),
    Output('lines-state', 'data', allow_duplicate=True),
    Output('clicked-edge-weight', 'value'),
    Input('graph', 'tapNodeData'), #Esto hace que se active el callback a clickear un nodo.
    State("weight-checklist", "value"),
    State('lines', 'data'),
    State('lines-state', 'data'),
    State('selected-nodes', 'data'),
    State("mod-checklist", "value"),
    State('graph-dict', 'data'),
    State('graph-dict-counter', 'data'),
    State('undo-state', 'data'),
    State('clicked-edge-weight', 'value'),
    prevent_initial_call=True
)
def highlight_nodes(tapped_node_data, weights, lines_data, lines_state, selected_nodes, modify, graph_dict, graph_dict_counter, undo_state, clicked_edge_weight):


    #Por defecto se mantienen las siguientes variables

    new_lines_state = lines_state

    new_clicked_edge_weight = clicked_edge_weight

    layout={'name': 'preset', 'fit': False}

    message = ''
            
    i = graph_dict_counter[0]
    g_dict = graph_dict[i]
    G = d_dict_to_nx(g_dict)

    new_undo_state = undo_state
    new_i = i



    new_selected_nodes = selected_nodes
    
    if weights: #Checklist marcado
        
        edge_style = [{'selector': 'edge', 'style': {'label': 'data(weight)', 'text-background-color': 'white',
                    'text-background-opacity': 0.8, 'curve-style': 'bezier','target-arrow-shape': 'triangle'}}]

    else: #Checklist no marcado
        
        edge_style = [{'selector': 'edge', 'style': {'curve-style': 'bezier','target-arrow-shape': 'triangle'}}]


    stylesheet = [
        {'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center',
                    'text-halign': 'center'}}
        ] + edge_style
    


    if modify: #Si está marcada la checklist de modificar grafo

        if tapped_node_data:
            node_id = tapped_node_data['id'] #id del nodo que se clickeó
            if node_id not in selected_nodes:
                new_selected_nodes.append(node_id)
            
            
        if len(new_selected_nodes) == 1: 

            message = 'Nodo ' + new_selected_nodes[0] + ' seleccionado.'   + ' \nSeleccione otro nodo para agregar la arista.'  

        if len(new_selected_nodes) == 2:

            try:

                if clicked_edge_weight:

                    w = int(clicked_edge_weight)

                else:
                    w = 1    

                assert ( w > 0 )     

                u = int(new_selected_nodes[0]) 
                v = int(new_selected_nodes[1])  
                G.add_weighted_edges_from([(u,v,w)]) #Se agrega la arista (u,v) con peso w    
                new_undo_state = True
                new_i = (i+1)%2

                new_selected_nodes = []

                new_lines_state = False

                new_clicked_edge_weight = ''

            except:

                new_selected_nodes = []

                message = 'Error en el input. Intente de nuevo.'




    else:    

        if not lines_state:          
            stylesheet = [
            {'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center',
                        'text-halign': 'center'}}
            ] + edge_style

            message = "Para la visualización debe actualizar las líneas."


        else: #lines_state=True                        
            pairdict =  lines_data[0]
            linedict = lines_data[1]
            l = lines_data[2]
            d = lines_data[3]
            n = lines_data[4]
            
            if l == n:
                
                lstr = 'Sí' #Hay línea universal
                
            else:

                lstr = 'No' #No hay línea universal
                
                
            
            
                    
            stylesheet = [
                {'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center',
                            'text-halign': 'center'}}
            ] + edge_style




            if tapped_node_data:
                node_id = tapped_node_data['id']
                if node_id not in selected_nodes:
                    new_selected_nodes.append(node_id)

            
            if len(new_selected_nodes) == 1: #Un nodo seleccionado
                message = 'Cantidad de líneas: '+ str(len(linedict.keys())) + '. Línea universal: ' + lstr + '. Diámetro: ' + str(d) + '.\n' + 'Nodo ' + new_selected_nodes[0] + ' seleccionado.'
            
            if len(new_selected_nodes) == 2: #Dos nodos seleccionados
                
                S=[int(new_selected_nodes[0]), int(new_selected_nodes[1])]

                
                key='('+ str(S[0])+','+ str(S[1])+')'  #Par
                

                line = pairdict[key] #Línea asociada al par
                
                stylesheet = [{'selector': 'node', 'style': {'label': 'data(label)', 'text-valign': 'center',
                    'text-halign': 'center'}}] + [{'selector': f'[id = "{v}"]', 'style': {'background-color': 'red'}} for v in line ] + edge_style #Se cambia el color de los vértices de la línea 
                message = 'Cantidad de líneas: '+ str(len(linedict.keys())) + '. Línea universal: ' + lstr + '. Diámetro: ' + str(d) + '.\n' + 'Línea '+ key + ' seleccionada.'+ '\nLínea: '+  str(line) + '.' + '\nPares generadores: ' + str(linedict[str(line)]) + '.'
                new_selected_nodes = [] #Se borran los nodos selccionados


    elements = nx_to_cytoscape_elements(G)

    new_graph_dict_counter = graph_dict_counter
    new_graph_dict_counter[0] = new_i

    new_g_dict = nx_to_dict(G)
    new_graph_dict = graph_dict
    new_graph_dict[new_i] = new_g_dict        

    
    return new_undo_state, new_graph_dict, new_graph_dict_counter, elements, layout, stylesheet, message, new_selected_nodes, new_lines_state, new_clicked_edge_weight


#Callback 7: Descargar
@app.callback(
    Output("download-info", "data"),
    Input("download-btn", "n_clicks"),
    State('lines', 'data'),
    State('lines-state', 'data'),
    State('graph-dict', 'data'),
    State('graph-dict-counter', 'data'),
    prevent_initial_call=True,
)
def donwnload(n_clicks, lines_data, lines_state, graph_dict, graph_dict_counter):

    i = graph_dict_counter[0]
    g_dict = graph_dict[i]
    G = d_dict_to_nx(g_dict)
    
    nodes = str(G.nodes())
    edges = str(G.edges(data=True))

    A = nx.to_numpy_array(G, dtype=int) #matriz de adyacencia
    strA = np.array2string(A, separator=', ') #String de la matriz de adyacencia


    if lines_state:
        pairdict =  lines_data[0]
        linedict = lines_data[1]
        strD = lines_data[5]
        strB = lines_data[6]

    else:
        pairdict =  ''
        linedict = ''
        strD = ''
        strB = ''

    content = 'Diccionario en formato de la aplicación: ' + str(g_dict) + '\n \n \n' + 'Nodos: '+ nodes + '\n \n' + 'Aristas: ' + edges + '\n \n \n' + 'Matriz de adyacencia: \n' + strA + '\n \n' + 'Matriz de distancias: \n' + strD +  '\n \n \n' + 'Betweenness: '+ strB + '\n \n \n' +  'Diccionario par-línea:  ' + str(pairdict) + '\n \n' +  'Diccionario línea-pares:  ' + str(linedict)
    
    
    return dict(content=content, filename="graphlines.txt")

    
if __name__ == '__main__':
    app.run(debug=True, port= 8050)
