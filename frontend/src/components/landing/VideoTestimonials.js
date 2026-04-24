import React, { useState } from 'react';
import { Play, X, Youtube } from 'lucide-react';

const TESTIMONIALS = [
  { id: 'JX7Bz64j9-E', title: 'Student Success Story' },
  { id: '6N7v5meXFSg', title: 'Student Experience' },
  { id: 'XHU08Zi7hP0', title: 'Learning Journey' },
];

const VideoTestimonials = ({ bg = '#F9FAFB', navy = '#1E3A5F' }) => {
  const [open, setOpen] = useState(null);

  return (
    <section className="py-16 md:py-20 px-4" style={{ background: bg }} id="video-testimonials" data-testid="video-testimonials">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-2 mb-3">
            <Youtube className="w-6 h-6 text-red-600" />
            <span className="text-sm uppercase tracking-widest text-red-600 font-semibold">Real stories</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold" style={{ color: navy }}>Hear from our students</h2>
          <p className="text-slate-600 mt-2">Quick clips from recent batches.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((t) => (
            <button
              key={t.id}
              onClick={() => setOpen(t)}
              data-testid={`testimonial-${t.id}`}
              className="group relative aspect-[9/16] rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all"
            >
              <img
                src={`https://img.youtube.com/vi/${t.id}/maxresdefault.jpg`}
                onError={(e) => { e.target.src = `https://img.youtube.com/vi/${t.id}/hqdefault.jpg`; }}
                alt={t.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="bg-white/90 backdrop-blur rounded-full w-16 h-16 flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg">
                  <Play className="w-7 h-7 text-red-600 ml-1" fill="currentColor" />
                </div>
              </div>
              <div className="absolute bottom-3 left-3 right-3 text-left">
                <div className="text-white font-semibold text-sm">{t.title}</div>
                <div className="text-white/80 text-xs">Tap to play</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {open && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-[100] p-4" onClick={() => setOpen(null)}>
          <div className="relative w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <button onClick={() => setOpen(null)} className="absolute -top-10 right-0 text-white hover:text-slate-200" data-testid="close-testimonial">
              <X className="w-7 h-7" />
            </button>
            <div className="aspect-[9/16] bg-black rounded-xl overflow-hidden shadow-2xl">
              <iframe
                src={`https://www.youtube.com/embed/${open.id}?autoplay=1&modestbranding=1&rel=0`}
                title={open.title}
                className="w-full h-full"
                allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
            <div className="text-center mt-3">
              <a
                href={`https://www.youtube.com/shorts/${open.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-white/90 hover:text-white text-sm underline"
              >
                Watch on YouTube
              </a>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default VideoTestimonials;
