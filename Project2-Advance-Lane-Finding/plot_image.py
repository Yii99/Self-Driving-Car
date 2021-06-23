import matplotlib.pyplot as plt

def plot(img_list, titles, row, column, figsize, fontsize, cmap, path):
    '''

    :param img_list: image list
    :param titles: titles of each image
    :param row: number of rows
    :param column: number of columns
    :param path: set a path to store the plot image
    :return:
    '''
    fig, axes = plt.subplots(row, column, figsize=figsize)
    for i, s_img_list in enumerate(img_list):
        for j, img in enumerate(s_img_list):
            axes[i, j].imshow(s_img_list[j], cmap=cmap)
            axes[i, j].axis('off')
            axes[i, j].set_title((titles[i][j]), fontsize=fontsize)
    fig.savefig(path)


