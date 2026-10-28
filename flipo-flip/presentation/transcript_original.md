# Presentation Transcript
1.  
Hi, I'm stelios, and today I will be presenting IYPT 2026 problem #6: The flipo flip

2.  
The problem statement reads: "A Flipo Flip toy can roll for multiple turns even though its shape is not circular. Investigate how its motion depeds on parameters such as geometry and initial release conditions" Our goal in this presentation is to understand the geometry of the toy, develop a theoretical model that connects relevant parameters and describes the motion of the toy, and test the model and our assumptions with experimental measurments.

3.  
Let's start with the geometry of the toy. To understand it, we will use the solid object called a steimnitz solid or a bicylinder. The steimnitz solid is the solid body obtained as the intersection of two cylinders of equal radius R at right angles.

4.  
The toy is obtained by getting the outer parts of a steimnitz solid - the part highlighted here on the top, and an identical one from the bottom - and gluing them together with a square prism of small width and round edges between them. Since the two cylinders that create the flipo flip via the steimnitz solid have the same axis of rotation during the movement of the toy, the total inertia of the toy around its main axis of rotation is the sum of the two moments of inertia of the two cylinders, and it is equal to mR^2, where m is the mass of each cylinder and R is its radius. The fact that this large surface is obtained from a steimnitz solid means that when the toy rolls in this side the contact point geometry is the same as if the cylinder of radius R was rolling.

5.  
Now, let's move on to the categorisation of the phases of motion of the toy. When the toy is rolling on a flat surface, we can think of them as a sequence of three repeating phases: Pure patch rolling, Ridge switch and Patch Switch.

6.  
Pure patch rolling is the part of the motion of the toy where the toy rolls along its large curved surface, in other words, its when the contact point remains on one cylindrical patch. As I mentioned before, during this phase of motion the contact geometry behaves exactly like a circular cylinder of radius R. One of the required assumptions for us to have a working model is the no slip constraint - the velocity of centre of mass to be equal to angular velocity times the radius of the cylinder - which is required for rolling motion to occur.

7.  
During this rolling motion, the only form of energy dissipation we can observe is from the rolling resistance between the flipo flip and the floor. The rolling resistance force is equal to the rolling coefficient multiplied by the weight of the bicylinder, the work done by it is the force times the distance travellled during pure patch rolling, and the distance traveled is equal to pi times R over 2. Dissipation from aerodynamic drag can be considered negligent considering the small velocities the toy achieves, and it is important to note that rolling resistance only accounts for dissipation of the initial translational energy, and the remaining rotational energy will be dissipated by other mechanisms like switching dissipation for the body to eventually come to rest.

8.  
Using the rolling resistance force, we can find how translational velocity u(t) is reduced during pure patch rolling. It is equal to the initial velocity minus the acceleration times time elapsed during pure patch rolling, where acceleration is the rolling resistance force devided by the effective mass of the toy. The effective mass of the toy is its mass plus a term that has two do with its rolling inertia.

9.  
Let's move on to the ridge switch part of the motion. It happens during pure patch rolling, when the contact point passes through the centre of the curved surface, which is also the the contact point of the two cylinders which we call ridge. Dissipation and mechanics in this point are accounted in pure patch rolling, and nothinf differs here, it's just important to be noted.

10.  
The third phase of the motion is the patch switch. During this part of the motion, the contact point is on either edges of the square prism here on the bottom, or on the enitre flat surface - which happens for an instant when it switches from the first to the second one. This phase sits between the end of pure patch rolling on one cylindrical patch, and the start of pure patch rolling on the other. When the contact point reaches the square edge between the patches, the pure rolling direction the toy can have jumps by 90 degrees. Two things might happen: If there's sufficient friction, the toy will smoothly reorient over finite time and continue rolling on the new patch with some additional loss of energy. 

(If asked: The 90 degree change is because the CM velocity was pointing toward the ground, and now it point to the left. Thats 90 degrees.)

11.  
But if friction is insufficient to provide the tangential impulse required for an instaltenous turn, the toy will slip and yaw, which dissipates energy quickly and stops the toy from doing any additional flips.

12.  
You cannot instantenously change the CM velocity vector from (u,0) to (0, u) - which is the 90 degree change I've been referring to - unless impulses of the right magnitude and direction are applied. The requested instanteneous 90 degree reorientation requires a large tangential impulse and a corresponding change in angular momentum. To calculate it, let's suppose the flipo flip is rolling along the x axis and we try ti convert its CM velocity to the y axis. We only care about the magnitude of the change so thats why we just chose two "random" orientations of 90 degree difference between them. So, we start with the change in momentum, which is mass times the difference of the 3D velocity vectors of the CM (3d dimention doesnt matter at all) for a 90 degree change. Using this we can find the magnitude of that change, equal to the square root of the sum of the squares of the initial and final momenta. Then we can find the change in angular momentum as the square root of the sum of squares of the initial and filan angular momenta, which are equal to the moments of inertia along the different axis respectively, times the angular velocity. We can convert the change in anular momentum to the impulse reuired for that change by dividing it with R. If we sum the required impulse for the change in angular momentum and translational momentum, we get the total impulse required J_req, which after some calculations is equal to square root of 2 times velocity times the efficient mass.

13.  
The only force that can provide that impulse is friction, thus we can define a dimensionless number Λ (Lambda), that compares the available fricitional impulse to the required impulse to make the patch switch. If Λ is much smaller than one, most of the energy will be lost during the switch and the movement will stop there. Generally, Λ is between 0 and 1 and it controls how much energy is dissipated during patch switch.

14.  
Let's move onto the full motion analysis. We've got the equations that we derived on pure patch rolling now rewritten, and the dissipation at patch switch equations. For pure patch rolling we've got acceleration equals minus friction force divided by effective mass, which is equal to k, and after some calculations equal to rolling friction coefficient times g over 2. And we've got the function that describes velocity decrease during pure rolling. For dissipation at patch switch, we've got that the velocity right after the patch switch is equal to the velocity before the patch switch times (1 - Λ). This is how Λ controls the energy dissipation for each patch switch. If we assume that it is constant for all switches then at the n-th switch we can find an equation that finds the velocity at the n-th switch after all the patch switches and pure rolling phases up to this point. 

15.  
In each pure patch rolling interval velocity evolves linearly, and then gets multiplied by a factor smaller than one for each patch switch. Velocity can only become zero during the linear decrease and not the percentile decrease of a patch switch, and therefore we get the equation for t_stop, when the flipo flip stops rolling further.

16.  
The stopping time will occur for the smaller nonnegative integer of n satisfying  u_n < kΔt. To get n in closed form, we solve the equality, wich results in the following solution for the continuous n.

17.  
These are the equations I explained, and from them we can theoretically predict the amount of patch switches the Flipo Flip will do before completely stopping. These are the equations used for the theoretical predictions in the tables you will see later in the experiments.

18.  
Now that we completed the theoretical model, let's move on to our experiments. For our setup, we used 6 flipo flips with different materials, mass and dimentions, a laser distance meter, tracker video analysis software, and a force gauge to apply different forces to the toy.

19.  
In oder theoretical model to predict the amount of flips that can be achieved before the movement ends, we experimentally measured the effective mass, the patch switch time and the rolling friction coefficient seperately for each flipo flip.

20.  
The first part of our analysis has to do with force application. We measure the number of flips the toy can do before sliping or stopping as a function of initial velocity, but how that velocity is obtained matters. We may apply a force in any of the visible locations,

21.  
and only some of them will initiate the motion.

22.  
Here, we can see all the locations the initial force was applied during our experiments, but only the green ones actually allowed the motion to start.

23.  
For each of the 6 flipo flips, the experiment went as follows: The flipo flip was placed upright, and a force was applied to the centre of the surface above the ridge using the force gauge. We used that force to induce an initial velocity measured by tracker. Then, we noted the number of flips the toy did before it stopped when it started with each initial velocity, creating the initial velocity - number of flips pairs that are visible on the diagram. This process was repeated enough times so that ten initial velocities - number of flips pairs were obtained. Each flipo flip has 10 such data points for each of two different surfaces. In other words, 20 experimental values were taken per flipo flip, ten on one type of surface and ten on another type of flat surface, in order to vary the rolling friction coefficient. We kept integer initial velocities from 2 meters per second up to 10 meters per second, plus 15 meters per second. Here you can see the two graphs that correspond to the two different surfaces the experiment was done for each flipo flip, with their experimentally measured friction coefficients, and a plot of the experimental and theoretical data points for each setup.

24.  
Our model generally overpredicts or matches the number of flips actually done in each experiment, and that's probably because there are some additional losses like air resistance or some minor deformations that might dissipate energy. Also the reason might be one of our assumptions, like the fact that we keep Λ constant, while experimentally it would be decreasing, and the fact that we consider t_switch constant, while it would be increasing with the number of flips because velocity decreases gradually requiring more time for each patrch switch, and it would allow for more time for energy dissipation. It's also about the no slip condition, because we assume the toy doesn't slip, so sometimes it may slip earlier than its initial energy would actually allow it to go if it weren't to slip, thus producing this kind of gap between the theoretical and experimental data.

25.  
Also we can see that there is a critical velocity for each flipo flip, after which the toy does no flips at all, while the model predicts an increasing number of flips. we will discuss that in a bit.

26.  
We can also see that when the friction coefficient is smaller, our model has a generally larger error. We believe that this has to do with the fact that we assume the no-slip condition, and when rolling friction coefficient is smaller it is easier for the toy to slip earlier than what the initial velocity would allow it in terms of available energy to do.

27.  
As you can see, the trends we discussed are maintained throughout all the flipo flips.

28.  
And this is our last flipo flip, which also has the smallest critical velocity. Time to adress the elephant in the room.

29.  
Why are there cases where 0 flips are done? In other words, why does a critical velocity exist? It's also because of the no slip condition assumption.

30.  
To model the toy's motion, we needed to assume that it actually rolls, but sometimes the no slip condition can't hold even from the start, because initial velocity is too much for the toy to keep contact with the ground, and it gets launched in the air!

31. Here's our bibliography,

32. And thank you very much for your attention!

33.  
(None)