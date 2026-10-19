import json,statistics as st
from collections import Counter,defaultdict
d=json.load(open('data.json')); T=d['teams']; P=d['players']
MDS=sorted({int(m) for t in T for m in t['o']['md']})
pn=lambda i:P.get(str(i),{}).get('t',i)
for t in T:
    t['md']={int(k):v for k,v in t['o']['md'].items()}
    t['cum']={}; s=0
    for m in MDS: s+=t['md'].get(m) or 0; t['cum'][m]=s
def ranks(key):
    arr=sorted(T,key=key); out={}; prev=None
    for i,t in enumerate(arr):
        v=key(t)
        if v!=prev: r=i+1; prev=v
        out[t['n']]=r
    return out
LR={m:ranks(lambda t,m=m:-t['cum'][m]) for m in MDS}
def name(t): return f"{t['n']} ({t['u']})"
# stage winners & ties
for m in [16,17]:
    best=max(t['md'].get(m) or 0 for t in T); w=[t['n'] for t in T if t['md'].get(m)==best]
    print('R',m,'winners',best,w)
for m in [16,17]:
    srt=sorted(T,key=lambda t:-t['cum'][m]); print('R',m,'leader',srt[0]['n'],srt[0]['cum'][m],'10th',srt[9]['n'],srt[9]['cum'][m],'gap',srt[0]['cum'][m]-srt[9]['cum'][m])
for nm in ['Bartativ FTeam','Speed Dragon Racing','Soleil noir Racing','Kinder Vamos','Aimerons Racing']:
    t=[x for x in T if x['n']==nm]
    for x in t: print(nm, {m:(LR[m][nm],x['cum'][m]) for m in [15,16,17]})

print('\n===== NEW STATS =====')
L=17; prevL=16
CH={1:'Limitless',2:'Wildcard',3:'Final Fix',4:'Autopilot',5:'No Negative',6:'3x Boost'}
OK={2:'wc',1:'ll',3:'ff',4:'ap',5:'nn',6:'x3'}
rr=lambda t,m: t['r'].get(str(m))
pts=[t['md'][L] for t in T if t['md'].get(L) is not None]
print('R17 avg',round(st.mean(pts)),'median',st.median(pts),'stdev',round(st.pstdev(pts)))
me=[t for t in T if t['n']=='Bartativ FTeam'][0]
print('me R17',me['md'][L],'pct teams below me', round(sum(p<me['md'][L] for p in pts)/len(pts)*100))
# movers
mv=sorted(T,key=lambda t:LR[prevL][t['n']]-LR[L][t['n']])
print('climbers',[(t['n'],LR[prevL][t['n']]-LR[L][t['n']],LR[L][t['n']]) for t in mv[::-1][:3]])
print('fallers',[(t['n'],LR[prevL][t['n']]-LR[L][t['n']],LR[L][t['n']]) for t in mv[:3]])
# global ranks
gr=sorted([(rr(t,L)[2],t['n']) for t in T if rr(t,L) and rr(t,L)[2]])
print('global overall rank best',gr[:3],'median',st.median([g for g,_ in gr]))
for th in [1000,10000,50000,100000]: print(' teams in global top',th,sum(g<=th for g,_ in gr))
gd=sorted([(rr(t,L)[1],t['n']) for t in T if rr(t,L) and rr(t,L)[1]])
print('best global stage rank R17',gd[:3])
# chips remaining in top10
top10=sorted(T,key=lambda t:-t['cum'][L])[:10]
print('chips left top10:')
for t in top10:
    left=[CH[c] for c in OK if not t['o'].get(OK[c])]
    print('  ',LR[L][t['n']],t['n'],len(left),left)
cl=Counter(); 
for t in T:
    for c in OK:
        if not t['o'].get(OK[c]): cl[CH[c]]+=1
print('chips still unused league-wide (teams):',cl.most_common())
print('avg chips left per team', round(sum(sum(1 for c in OK if not t['o'].get(OK[c])) for t in T)/len(T),2))
# chip effectiveness: avg points on races with chip vs without, per chip
eff=defaultdict(list)
for t in T:
    for m in MDS:
        r=rr(t,m)
        if not r or t['md'].get(m) is None: continue
        avg=st.mean([x['md'][m] for x in T if x['md'].get(m) is not None])
        eff[r[9]].append(t['md'][m]-avg)
print('chip uplift vs race avg:',{CH.get(k,'none'):(round(st.mean(v)),len(v)) for k,v in eff.items()})
# ownership R17 & differentials
own=Counter(); capc=Counter()
n=0
for t in T:
    r=rr(t,L)
    if not r: continue
    n+=1; ids=[i for i in str(r[13]).split('.') if i]
    if r[14]: ids=[i for i in ids if i!=str(r[14])]
    own.update(ids); capc[str(r[11] or r[10])]+=1
pp=d['ppts'].get(str(L),{})
print('ownership R17:',[(pn(i),round(c/n*100),pp.get(i)) for i,c in own.most_common(12)])
diff=[(pn(i),round(own[i]/n*100),pp[i]) for i in pp if pp[i]>=25 and own[i]/n<0.2]
print('differentials (>=25pts, <20% owned):',diff)
miss=[(pn(i),pp[i],round(own[i]/n*100)) for i in sorted(pp,key=lambda i:-pp[i])[:5]]
print('top scorers & ownership:',miss)
print('captains R17:',[(pn(i),round(c/n*100),pp.get(i)) for i,c in capc.most_common(5)])
# template team
tmpl=Counter()
for t in T:
    r=rr(t,L)
    if r: tmpl[tuple(sorted(str(r[13]).split('.')))]+=1
top=tmpl.most_common(1)[0]; print('most common exact lineup',[pn(i) for i in top[0]],top[1])
# extra subs penalties season
pen=[]
for t in T:
    ex=0; inact=0
    for m in MDS:
        r=rr(t,m)
        if not r: continue
        if r[9] not in (1,2): ex+=max(0,(r[7] or 0)-(r[8] or 0))
        inact+=r[12] or 0
    pen.append((ex*10,inact,t['n']))
pen.sort(reverse=True)
print('extra-sub penalty season top',pen[:3],'league total',sum(p[0] for p in pen),'teams with 0',sum(1 for p in pen if p[0]==0))
print('R17 extra sub penalties total', sum(max(0,(rr(t,L)[7] or 0)-(rr(t,L)[8] or 0))*10 for t in T if rr(t,L) and rr(t,L)[9] not in (1,2)))
inl=sorted(pen,key=lambda p:p[1])[:3]; print('inactive driver penalties worst',inl)
# budget
bud=sorted([(rr(t,L)[6],t['n']) for t in T if rr(t,L) and rr(t,L)[6]],reverse=True)
print('budget top',bud[:3],'bottom',bud[-3:],'league avg',round(st.mean(b for b,_ in bud),1),'top10 avg',round(st.mean(rr(t,L)[6] for t in top10),1))
# consistency & records
cons=[]
for t in T:
    v=[t['md'][m] for m in MDS if t['md'].get(m) is not None]
    if len(v)==len(MDS): cons.append((round(st.pstdev(v)),min(v),t['n']))
print('most consistent',sorted(cons)[:3],'highest floor',sorted(cons,key=lambda x:-x[1])[:3])
top10count=Counter()
for m in MDS:
    srt=sorted([t for t in T if t['md'].get(m) is not None],key=lambda t:-t['md'][m])[:10]
    top10count.update(t['n'] for t in srt)
print('most stage top-10 finishes',top10count.most_common(4))
wins=Counter()
for m in MDS:
    b=max(t['md'].get(m) or 0 for t in T); wins.update(t['n'] for t in T if t['md'].get(m)==b)
print('stage wins',wins.most_common(5))
lead=Counter(sorted(T,key=lambda t:-t['cum'][m])[0]['n'] for m in MDS)
print('races as leader',lead.most_common())
rec=max(((t['md'][m],m,t['n']) for t in T for m in MDS if t['md'].get(m) is not None)); print('season record',rec)
# form last 5
f5=sorted(T,key=lambda t:-sum(t['md'].get(m) or 0 for m in MDS[-5:]))[:5]
print('form last5',[(t['n'],sum(t['md'].get(m) or 0 for m in MDS[-5:]),LR[L][t['n']]) for t in f5])
f3=sorted(T,key=lambda t:-sum(t['md'].get(m) or 0 for m in MDS[-3:]))[:3]
print('form last3',[(t['n'],sum(t['md'].get(m) or 0 for m in MDS[-3:])) for t in f3])
# gaps
s=sorted(T,key=lambda t:-t['cum'][L])
print('gaps 1-2',s[0]['cum'][L]-s[1]['cum'][L],'1-3',s[0]['cum'][L]-s[2]['cum'][L],'3-4',s[2]['cum'][L]-s[3]['cum'][L])
# me vs avg
print('me above league avg in races', sum(1 for m in MDS if me['md'][m]>st.mean([x['md'][m] for x in T if x['md'].get(m) is not None])),'of',len(MDS))
print('me stage ranks',[ (m,sorted([x['md'].get(m) or -1 for x in T],reverse=True).index(me['md'][m])+1) for m in MDS[-5:]])
# value growth season
vg=sorted([(round(rr(t,L)[6]-100,1),t['n']) for t in T if rr(t,L) and rr(t,L)[6]],reverse=True)[:3]; print('budget growth top',vg)
