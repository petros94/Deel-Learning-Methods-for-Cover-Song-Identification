import imp
import torch
import random
import numpy as np
from utils.generic import generate_triplets, get_device, retrieve_repr, repr_triplet_2_segments, frame_idx_2_time, sample_songs, segment_and_scale

class HardTripletDataset(torch.utils.data.Dataset):
    def __init__(self, songs, n_batches=256, songs_per_batch=64, frame_size=400, scale=(1, 0.33)):
        self.n_batches = n_batches
        self.songs_per_batch = songs_per_batch
        
        """
        {
            "120345 (song_id)": torch.tensor of size num_segs X num_covers X 1 X num_features X frame_size
        }
        """
        song_segs = {}
        for song_id, covers in songs.items():
            segs = []
            for cover in covers:
                repr = cover['repr']
                frames = segment_and_scale(repr, frame_size=frame_size, scale=scale)
                segs.append(frames)
                
            # Find minimum length
            min_len = min(list(map(lambda i: len(i), segs)))

            # Crop to minimum length
            segs = [seg[: min_len - 1] for seg in segs]
            
            # Size num_segs X num_covers X 1 X num_features X frame_size
            ret = torch.stack(segs, dim=1).unsqueeze(2)
            song_segs[song_id] = ret
            
        
        # Create batches
        # Each sample contains P songs of K covers each
        self.batches = []
        self.total_samples = 0
        for b in range(self.n_batches):
            samples = []
            labels = []
            P = sample_songs(songs, self.songs_per_batch).keys()
            
            for song_id in P:
                K = random.choice(song_segs[song_id]) #Select a random part of the songs
                samples.append(K)
                labels.extend([song_id]*K.size(0))
                self.total_samples += K.size(0)
                
            # Samples are now a tensor of size P*K X 1 X num_features X frame_size
            samples = torch.cat(samples)
            labels = np.array(labels)
            
            assert samples.dim() == 4
            
            self.batches.append((samples, labels))
            
        print(f"Total samples: {self.total_samples}")
        
    def __getitem__(self, idx):
        return self.batches[idx]
    
    def __len__(self):
        return len(self.batches)