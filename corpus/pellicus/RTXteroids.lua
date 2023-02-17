-- MIT License
-- Copyright (c) 2023 Dario Pelella

-- Permission is hereby granted, free of charge, to any person obtaining a copy
-- of this software and associated documentation files (the "Software"), to deal
-- in the Software without restriction, including without limitation the rights
-- to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
-- copies of the Software, and to permit persons to whom the Software is
-- furnished to do so, subject to the following conditions:

-- The above copyright notice and this permission notice shall be included in all
-- copies or substantial portions of the Software.

-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
-- AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
-- OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
-- SOFTWARE.

doci=0


function TIC()
    t = time() / 2e3
    S = math.sin(t)
    C = math.cos(t)

    W =1+(t/4) % 3 //1

    t=2*t
    S2 = math.sin(t)
    C2 = math.cos(t)
  
    Kx,Ky,Kz = C*4,-1,-6
    
    t = 1/(Kx^2 + Ky^2 + Kz^2)^.5
    Kx,Ky,Kz = Kx*t ,Ky*t ,Kz*t
    
    Sx,Sy,Sz = 2*C,C/2+4,12+2*S

    Ax,Ay,Az = 2*S,2*S+1,20+4*C
    Bx,By,Bz  =-S*3,0.3,10
    R = 1
    SR = 1 + W/10
    if W==2 then
        R=4
        Ax,Ay,Az = 0,-2,25
        Bx,By,Bz  =0,8,25
        Sx,Sy,Sz = C2*7,C*3+2,25+S2*7
    end
    R2=R*R



    for o = 0, 32400  do
        Ox,Oy,Oz = S,-C+3,C
        rx,ry,rz =(o % 240 -120) / 240,(80  -o / 240 ) / 240 -.1,1
        t = 1/(rx^2 + ry^2 + 1)^.5
        rx,ry,rz = rx*t ,ry*t , t

        c,d,doci= 0,80,0
        res,lit,sss=0,0,0

        mz = Kx*rx+Ky*ry+Kz*rz
  
    if W==1 then
        if  mz < 0.01 then
            nx,ny,nz = 4+Ox ,2-Oy ,44-Oz
            t = (Kx*nx+Ky*ny+Kz*nz)/mz
            if t<d then 
                c=2
                d=t
            end
        end
    end  
    ::ray::    
        if  ry < 0 then
            t = -(Oy + 2) / ry
            if  t < d then
                d = t
                c = 1
            end
        end
        
        ::shdpass::

        nx,ny,nz=Sx-Ox ,Sy-Oy ,Sz-Oz 
        t = rx*nx+ry*ny+rz*nz
        if t>0 then
                y = (nx^2+ny^2+nz^2) - t^2
                if y < SR*SR then
                    t = t-(SR*SR - y)^.5 
                    if t < d then
                        d = t
                        c = 3
                    end
                end
            end

        if doci<2 then
-- XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
            ix,iy,iz=Ox-Ax,Oy-Ay,Oz-Az
            nx,ny,nz=Bx-Ax,By-Ay,Bz-Az
            lx =  nx^2+ny^2+nz^2   
            ly =  rx*nx+ry*ny+rz*nz        
            lz =  ix*nx+iy*ny+iz*nz       
        
            k2 = lx - ly^2
            k1 = lx*(ix*rx+iy*ry+iz*rz) -  lz*ly
            k0 = lx*(ix^2+iy^2+iz^2) -  lz^2 - R2*lx
               
            h = k1*k1 - k2*k0
            if  h<0 then 
                goto noci
            end
        

            h = h^.5
             t = (-k1-h)/k2
            y = lz + t*ly



            if y>0 and y<lx then 
                 y = y/lx
                 oor=1/R
                 Nx,Ny,Nz = (ix+rx*t-nx*y)*oor ,(iy+ry*t-ny*y)*oor,(iz+rz*t-nz*y)*oor
                goto okci
            end   
            t = (( y<0 and 0 or lx) -   lz)/ly
            if math.abs(k1+k2*t)<h then
                f = y >0 and 1 or -1
                f = f / lx^.5

                Nx,Ny,Nz = nx*f ,ny*f ,nz*f
                goto okci                
            end  

            goto noci
      ::okci::      
            if  t < d then
                d = t
                c=4
                end

-- XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        ::noci::
        end



        if sss>0 then

            lit = d>90 and math.max(0,lit-2) or lit
            goto shdok
        end

        if c>0 then 
            ix,iy,iz = Ox+rx*d ,Oy+ry*d ,Oz+rz*d
            t = 1/((10-ix)^2+(10-iy)^2+(5-iz)^2)^.5
            lx,ly,lz=(10-ix)*t,(10-iy)*t,(5-iz)*t
            Ox,Oy,Oz = ix,iy,iz
            if c==1 then
                res = 1 + ((ix//4+iz//4)&1)*8 
                lit= ly*4
                goto shd
            end
            if c==2 then
                if ix<-8 or ix>8 or iy<-1 or iy>8 then
                    goto nope
                end
                res = 8
                t = -2*mz
                rx,ry,rz = rx + Kx*t  , ry + Ky*t  , rz + Kz*t
                c,d=0,80
                goto ray
    
            end
            if c==3 then

                lit = (ix-Sx)*lx +(iy-Sy)*ly+(iz-Sz)*lz
                res = 15 - math.max(0,lit/SR*3)
                
                goto nope
            end

            if c==4 then
           
    --            trace(c)
                lit = (Nx*lx +Ny*ly+Nz*lz)*4
                doci=4

                if W>1 then
                    res,t=8,-2*(Nx*rx +Ny*ry+Nz*rz)
                    rx,ry,rz = rx + Nx*t , ry + Ny*t  , rz + Nz*t
                    c=0 d=80
                    goto ray
                end
               res = 9
            end

            goto shd
        end
        goto nope
  ::shd::

        rx,ry,rz = lx,ly,lz
        d=80  c=0
        sss =1
        goto shdpass
::shdok::
        res = res + lit


        ::nope::
        poke4(o,res)
    end
    end
    
    
    
-- <PALETTE>
-- 000:000000482065b13e53ef7d57ffcd75a7f07038b76425717929366f3b5dc941a6f673eff7ffffff94b0c2566c86333c57
-- </PALETTE>