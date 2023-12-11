import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import SpectralClustering

# 生成示例的二维矩阵数据
matrix_data = np.random.rand(10, 10)

# 使用 Spectral Clustering 进行聚类
n_clusters = 3
spectral_clustering = SpectralClustering(n_clusters=n_clusters, affinity='nearest_neighbors', random_state=0)
labels = spectral_clustering.fit_predict(matrix_data)
print(labels)
# # 绘制聚类结果
# plt.imshow(matrix_data, cmap='viridis')
# plt.title('Original Matrix')
# plt.show()

# # 绘制聚类结果
# plt.scatter(range(len(labels)), [0] * len(labels), c=labels, cmap='viridis', s=100)
# plt.title('Spectral Clustering Result')
# plt.show()