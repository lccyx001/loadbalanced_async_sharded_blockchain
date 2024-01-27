import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import SpectralClustering
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

adjacency_matrix = np.array([[0,3,1,0,0],
                             [3,0,4,0,5],
                             [1,4,0,10,2],
                             [0,0,10,0,6],
                             [0,5,2,6,0]])

csr_adj_matrix = csr_matrix(adjacency_matrix)
csr_trans_matrix = csr_matrix(adjacency_matrix.transpose())
simility_matrix = cosine_similarity(csr_adj_matrix,csr_trans_matrix)
print(simility_matrix)