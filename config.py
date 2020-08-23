
import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
import gensim



# load model
print ("Loading model:word2vec ......")
w2v_model = gensim.models.KeyedVectors.load_word2vec_format('./word2vec/news_12g_baidubaike_20g_novel_90g_embedding_64.bin', binary=True, limit=1000000)
#w2v_model = gensim.models.Word2Vec.load('./word2vec/.model')
