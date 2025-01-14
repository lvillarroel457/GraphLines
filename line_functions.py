import numpy as np
import networkx as nx


def FW(G):
    '''
    Floyw Warshall
    
    '''

    D = nx.floyd_warshall_numpy(G)

    return D



def Betweenness(A):
    
    '''

    Recibe una matriz de distancias (numpy array) de un espacio cuasimétrico y retorna la betweenness en una lista.
    
    '''
    
    assert np.shape(A)[0] == np.shape(A)[1]

    B = []
    
    n = np.shape(A)[0]
    
    for k in range(n):
        for i in range(n):
            for j in range(n):

                if k!=i and i!=j and j!=k:

                    if A[i,k] + A[k,j] == A[i,j]:
                        
    
                        B.append((i,k,j))

        
    return B


def lines(B, n):

    '''
    Implementación del algoritmo anterior (salvo que a la línea L(i,j) no se le agrega {i,j}).
    
    Recibe la betweenness de un espacio cuasimétrico en una lista (B) y la cantidad de puntos del espacio (n).
    Retorna las líneas del espacio en el siguiente formato:
    Un tensor de n x n x n, donde la posición k,i,j vale 1 si k está en la línea generada por (i,j) y vale 0 si no.
    '''

    LM = np.zeros((n,n,n))
    
    for b in B:
        
        (i,k,j) = b

        
        LM[i,k,j] = 1
        LM[k,i,j] = 1
        LM[j,i,k] = 1

                        


    return LM


def matrixtolinesdict(LM, n, metric = False):

    '''
    Recibe: Un tensor de n x n x n, donde la posición k,i,j vale 1 si k está en la línea generada por (i,j) y vale 0 si no (LM).
            La cantidad de puntos del espacio (n).
            Un valor de verdad (metric).
            
    Retorna: Dos diccionarios pairdict y linedict y un entero m. pairdict tiene a todos los pares (en formato de lista como string, por ej. '(3,5)') como llaves y cada par tiene una lista con su línea generada como valor.
             linedict tiene a todas las líneas (en formato de lista como string, por ej. '[1,3,4]') como llaves y cada línea tiene una lísta con todos sus pares generadores como valor.
             m es el largo de la línea más grande.
             Si metric = True solo se consideran los pares [i,j] con i < j.
    '''

    pairdict = {}
    linedict = {}
    m = 0 


    for i in range(n):

        if metric:
            
            l = i+1
        else:
        
            l = 0
            
        for j in range(l, n):

            if i != j:
                
                L1 = [i,j]
            
                for k in range(n):
    
                    if LM[k,i,j] == 1:
    
                        L1.append(k)

            
                L1.sort()

                if len(L1) > m:
                    
                    m = len(L1)

                pair='(' + str(i) + ','+ str(j)+')'
                
                pairdict[pair] = L1


                if str(L1) in linedict.keys():
                    
                    linedict[str(L1)].append(pair)
                
                else:   

                    linedict[str(L1)] = [pair]
                


    return pairdict, linedict, m 


