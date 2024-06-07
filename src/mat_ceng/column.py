from dataclasses import dataclass
import math

@dataclass
class Material:
    fc: float = 50 # specified compressive strength of concrete, MPa
    fy: float = 420 # specified yield strength for nonprestressed reinforcement, MPa
    wc: float = 2500 # density, unit weight, of normalweight concrete, kg/m³

@dataclass
class Section_Dimensions:
    # Note that the dimension c33 is the depth of the Section in the 2-2 direction and contributes primarily to I33.
    section_c22:float # cross section width, mm
    section_c33 :float # cross section depth, mm
    section_cc :float # 20.5.1.3 clear cover of reinforcement, mm
    rft_ratio :float # reinforcements ratio of longitudinal bars

@dataclass
class Load_Case:
    # factored axial force; to be taken as positive for compression and negative for tension, N
    Pu :float # ultimate design axial force, N
    Pu_sustained:float # ultimate sustained axial force, N
    Mu_22 :float # ultimate desigm moment about local axis 2-2 as per ETABS, N*mm
    Mu_33 :float  # ultimate desigm moment about local axis 3-3 as per ETABS, N*mm

    def import_from_etabs(self, 
                          force_unit_scale:float = 1e3, 
                          moment_unit_scale:float = 1e6, 
                          flip_axial_sign:bool = True,
                          moment_absolute:bool = True) :
        self.Pu *= force_unit_scale
        self.Pu_sustained *= force_unit_scale
        self.Mu_22 *= moment_unit_scale
        self.Mu_33 *= moment_unit_scale
        if flip_axial_sign:
            self.Pu *= -1
            self.Pu_sustained *= -1
        if moment_absolute:
            self.Mu_22 = abs(self.Mu_22)
            self.Mu_33 = abs(self.Mu_33)
        return self

@dataclass
class Column():
    lu_22:float # unsupported length of column or wall, mm
    lu_33:float # unsupported length of column or wall, mm
    k_22:float #effective length factor for compression members
    k_33:float #effective length factor for compression members

def calculate_column_actual_moment_of_inertia(material:Material, dimensions:Section_Dimensions, loads:Load_Case,rounding_digits:int = 3) -> float:
    '''
    calculate moments of inertia for elastic analysis at factored load
    as per ACI318-19 Table 6.6.3.1.1(b)
    '''
    Ag = dimensions.section_c22 * dimensions.section_c33 # gross area of concrete section, mm²
    Ast = Ag * dimensions.rft_ratio # total area of longitudinal reinforcement bars, mm²
    Po = 0.85 * material.fc * (Ag - Ast) + material.fy * Ast # 22.4.2.2 nominal axial strength at zero eccentricity, N

    Ig_22 = dimensions.section_c33 * dimensions.section_c22**3 / 12 # moment of inertia of gross concrete section about centroidal axis, neglecting reinforcement, mm⁴
    Ig_33 = dimensions.section_c22 * dimensions.section_c33**3 / 12 # moment of inertia of gross concrete section about centroidal axis, neglecting reinforcement, mm⁴

    I22_calculated = (0.8 + 25 * Ast / Ag)*(1 - (loads.Mu_22/(loads.Pu*dimensions.section_c22)) - 0.5 * (loads.Pu/Po)) * Ig_22 # Table 6.6.3.1.1(b)
    I33_calculated = (0.8 + 25 * Ast / Ag)*(1 - (loads.Mu_33/(loads.Pu*dimensions.section_c33)) - 0.5 * (loads.Pu/Po)) * Ig_33 # Table 6.6.3.1.1(b)
    if loads.Pu <= 0:
        I22_calculated = 0.35 * Ig_22
        I33_calculated = 0.35 * Ig_33
    I22 = max(min(I22_calculated,0.875 * Ig_22),0.35 * Ig_22)
    I33 = max(min(I33_calculated,0.875 * Ig_33),0.35 * Ig_33)

    return {'moment_of_inertia':(round(I22,rounding_digits),round(I33,rounding_digits)), 
            'ratio':(round(I22/Ig_22,rounding_digits),round(I33/Ig_33,rounding_digits))}


def calculate_effective_flexural_stiffness(Ec:float,
                                           Ig:float,
                                           I:float,
                                           betta_dns:float = 0.7,
                                           equation_a = False,
                                           equation_c = False):
    '''
    (EI)eff, N*mm²

    betta_dns = ratio used to account for reduction of stiffness of columns due to sustained axial loads
    '''
    if equation_a:
        return ((0.4*Ec*Ig)/(1+betta_dns)) # (6.6.4.4.4a)
    elif equation_c:
        return ((Ec*I)/(1+betta_dns)) # (6.6.4.4.4c)

def calculate_critical_buckling_load(EI_eff: float,
                                     k:float,
                                     lu:float):
    '''
    Pc, N
    lu, unsupported length of column or wall, mm
    k, effective length factor for compression members
    '''
    Pc = (((math.pi)**2 * EI_eff)/(k*lu)**2) # (6.6.4.4.2)
    return Pc


def calculate_column_delta_non_sway(Pu:float,
                                    Pc:float,
                                    Cm:float = 1.0):
    '''
    delta_non_sway = moment magnification factor used to reflect effects of member curvature between ends of a compression member

    Cm: factor relating actual moment diagram to an equivalent uniform moment diagram
    '''
    delta_non_sway = ((Cm)/(1-(Pu/(0.75 * Pc)))) # (6.6.4.5.2)
    delta_non_sway = max(delta_non_sway,1)
    return delta_non_sway

def calculate_minor_delta_ns(column:Column,
                             material:Material,
                             dim:Section_Dimensions,
                             load:Load_Case,
                             Cm:float = 1,
                             rounding_digits:int = 3):
    I_calculated = calculate_column_actual_moment_of_inertia(
        material=material,
        dimensions=dim,
        loads=load,
        rounding_digits=rounding_digits
    )
    I = I_calculated['moment_of_inertia'][0] # 0 = minor, 1 = Major
    Ig = I / I_calculated['ratio'][0]
    Ec = 4700 * math.sqrt(material.fc)
    betta_dns = min(1, load.Pu_sustained / load.Pu)
    EI_eff_a = calculate_effective_flexural_stiffness(Ec,Ig,I,betta_dns,equation_a=True)
    EI_eff_c = calculate_effective_flexural_stiffness(Ec,Ig,I,betta_dns,equation_c=True)
    Pc_a = calculate_critical_buckling_load(EI_eff_a,column.k_22, column.lu_22)
    Pc_c = calculate_critical_buckling_load(EI_eff_c,column.k_22, column.lu_22)
    delta_ns_a = calculate_column_delta_non_sway(load.Pu,Pc_a,Cm)
    delta_ns_c = calculate_column_delta_non_sway(load.Pu,Pc_c,Cm)
    return {'Etabs': delta_ns_a, 'Method C':delta_ns_c}


def calculate_major_delta_ns(column:Column,
                             material:Material,
                             dim:Section_Dimensions,
                             load:Load_Case,
                             Cm:float = 1,
                             rounding_digits:int = 3):
    I_calculated = calculate_column_actual_moment_of_inertia(
        material=material,
        dimensions=dim,
        loads=load,
        rounding_digits=rounding_digits
    )
    I = I_calculated['moment_of_inertia'][1] # 0 = minor, 1 = Major
    Ig = I / I_calculated['ratio'][1]
    Ec = 4700 * math.sqrt(material.fc)
    betta_dns = min(1, load.Pu_sustained / load.Pu)
    EI_eff_a = calculate_effective_flexural_stiffness(Ec,Ig,I,betta_dns,equation_a=True)
    EI_eff_c = calculate_effective_flexural_stiffness(Ec,Ig,I,betta_dns,equation_c=True)
    Pc_a = calculate_critical_buckling_load(EI_eff_a,column.k_33, column.lu_33)
    Pc_c = calculate_critical_buckling_load(EI_eff_c,column.k_33, column.lu_33)
    delta_ns_a = calculate_column_delta_non_sway(load.Pu,Pc_a,Cm)
    delta_ns_c = calculate_column_delta_non_sway(load.Pu,Pc_c,Cm)
    return {'Etabs': delta_ns_a, 'Method C':delta_ns_c}