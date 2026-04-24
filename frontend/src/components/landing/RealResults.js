import React from 'react';
import { Trophy, Award, Star } from 'lucide-react';

const RESULTS = [
  {
    name: 'Harshit',
    achievement: 'AIR 916',
    exam: 'JEE Advanced',
    college: 'IIT Guwahati',
    icon: Trophy,
    accent: 'from-amber-400 to-orange-500',
    quote: "NexUacademy's Chemistry coaching was exceptional. The concepts were crystal clear and practice problems were JEE-level.",
  },
  {
    name: 'Tanishq Saxena',
    achievement: 'AIR 341',
    exam: 'JEE Advanced',
    college: 'IIT Kharagpur',
    icon: Award,
    accent: 'from-indigo-500 to-purple-600',
    quote: "Nitin Sir's teaching methodology helped me secure a top 500 rank. Highly recommended!",
  },
  {
    name: 'Samyak Rai',
    achievement: 'INCHO Qualifier',
    exam: 'Chemistry Olympiad',
    college: 'IIT Hyderabad',
    icon: Star,
    accent: 'from-emerald-400 to-teal-600',
    quote: 'The Olympiad preparation at NexUacademy was outstanding. Made it to INCHO!',
  },
];

const RealResults = ({ navy = '#1E3A5F' }) => (
  <section className="py-16 md:py-20 px-4 bg-white" id="results" data-testid="real-results">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-10">
        <h2 className="text-3xl sm:text-4xl font-extrabold" style={{ color: navy }}>Our students' achievements</h2>
        <p className="text-slate-600 mt-2">Real students. Real ranks. Real IITs.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {RESULTS.map((r) => {
          const Icon = r.icon;
          return (
            <div key={r.name} className="bg-white rounded-2xl shadow-lg hover:shadow-2xl transition overflow-hidden border border-slate-100" data-testid={`result-${r.name.replace(/\s+/g, '-')}`}>
              <div className={`bg-gradient-to-r ${r.accent} p-5 text-white flex items-center justify-between`}>
                <Icon className="w-10 h-10 opacity-90" />
                <div className="text-right">
                  <div className="text-2xl font-extrabold">{r.achievement}</div>
                  <div className="text-xs opacity-90">{r.exam}</div>
                </div>
              </div>
              <div className="p-5">
                <div className="font-bold text-slate-900 text-lg">{r.name}</div>
                <div className="text-sm text-slate-500 mb-3 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" /> {r.college}
                </div>
                <p className="text-slate-700 italic text-sm border-t pt-3">"{r.quote}"</p>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 rounded-2xl p-6">
        <div className="text-center">
          <div className="text-3xl font-extrabold text-indigo-600">3+</div>
          <div className="text-sm text-slate-600">Top 1000 AIR ranks</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-extrabold text-emerald-600">IIT</div>
          <div className="text-sm text-slate-600">Guwahati · Kharagpur · Hyderabad</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-extrabold text-purple-600">INCHO</div>
          <div className="text-sm text-slate-600">Chemistry Olympiad qualifier</div>
        </div>
      </div>
    </div>
  </section>
);

export default RealResults;
