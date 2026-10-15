import React, { useEffect, useState } from 'react';
import { Youtube, Play } from 'lucide-react';
import api from '../../utils/api';

const YouTubeSection = ({ navy = '#1E3A5F' }) => (
  <section className="py-16 md:py-20 px-4 bg-gradient-to-br from-red-50 to-orange-50" id="youtube" data-testid="youtube-section">
    <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-10 items-center">
      <div className="aspect-video rounded-2xl overflow-hidden shadow-2xl bg-black">
        <iframe
          src="https://www.youtube.com/embed/videoseries?list=UU6nS44IoXkv3Bx9kPeFt1fQ"
          title="NexUacademy YouTube channel"
          className="w-full h-full"
          loading="lazy"
          allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Youtube className="w-6 h-6 text-red-600" />
          <span className="text-xs uppercase tracking-widest text-red-600 font-semibold">YouTube</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold mb-4" style={{ color: navy }}>Free lessons on YouTube</h2>
        <ul className="space-y-3 mb-6">
          {[
            { t: 'Free Chemistry lessons', d: 'Concept videos + problem walk-throughs' },
            { t: 'JEE tips & tricks', d: 'Shortcuts, exam strategy, revision plans' },
            { t: 'Weekly live sessions', d: 'Doubt-clearing Q&A with Nitin Sir' },
          ].map((it, i) => (
            <li key={i} className="flex items-start gap-3">
              <div className="w-6 h-6 bg-red-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                <Play className="w-3 h-3 text-white" fill="currentColor" />
              </div>
              <div>
                <div className="font-semibold text-slate-900">{it.t}</div>
                <div className="text-sm text-slate-600">{it.d}</div>
              </div>
            </li>
          ))}
        </ul>
        <a
          href="https://www.youtube.com/@NexUacademypvtltd?sub_confirmation=1"
          target="_blank"
          rel="noopener noreferrer"
          data-testid="youtube-subscribe-btn"
          className="inline-flex items-center gap-2 px-6 py-3 bg-red-600 text-white font-bold rounded-xl hover:bg-red-700 hover:scale-[1.02] transition-all shadow-lg"
        >
          {embedUrl ? (
            <iframe
              src={embedUrl}
              title={title || 'NexUacademy latest video'}
              className="w-full h-full"
              loading="lazy"
              allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-white/70 text-sm">
              Loading latest video…
            </div>
          )}
        </div>
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Youtube className="w-6 h-6 text-red-600" />
            <span className="text-xs uppercase tracking-widest text-red-600 font-semibold">
              Latest on YouTube
            </span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-4" style={{ color: navy }}>
            {title || 'Free lessons on YouTube'}
          </h2>
          <ul className="space-y-3 mb-6">
            {[
              { t: 'Free Chemistry lessons', d: 'Concept videos + problem walk-throughs' },
              { t: 'JEE tips & tricks', d: 'Shortcuts, exam strategy, revision plans' },
              { t: 'Weekly live sessions', d: 'Doubt-clearing Q&A with Nitin Sir' },
            ].map((it, i) => (
              <li key={i} className="flex items-start gap-3">
                <div className="w-6 h-6 bg-red-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                  <Play className="w-3 h-3 text-white" fill="currentColor" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">{it.t}</div>
                  <div className="text-sm text-slate-600">{it.d}</div>
                </div>
              </li>
            ))}
          </ul>
          <a
            href="https://www.youtube.com/@NexUacademypvtltd?sub_confirmation=1"
            target="_blank"
            rel="noopener noreferrer"
            data-testid="youtube-subscribe-btn"
            className="inline-flex items-center gap-2 px-6 py-3 bg-red-600 text-white font-bold rounded-xl hover:bg-red-700 hover:scale-[1.02] transition-all shadow-lg"
          >
            <Youtube className="w-5 h-5" /> Subscribe — it's free
          </a>
        </div>
      </div>
    </section>
  );
};

export default YouTubeSection;
